from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path

from ada.compositions.manager_surface import AdaManagerSurfaceComposition
from ada.compositions.surface import AdaSurfaceRegistry, resolve_ada_surface
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST, ToolManifestResolution
from ada.ui.shell.navigation import create_ada_navigation_module
from atlanticus.web.assets import AssetLayer
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.models import ApplicationMetadata, WebApplicationDefinition
from atlanticus.web.modules import WebModule
from integrated_operations.application.layout import build_application_layout
from integrated_operations.application.models import IntegratedOperationsApplicationComposition
from integrated_operations.application.presentation import create_unified_presentation_module
from integrated_operations.surface import IntegratedOperationsSurfaceAdapter

_APPLICATION_ROOT = Path(__file__).resolve().parents[1]

APPLICATION_ASSET_LAYER = AssetLayer(
    name='ada_integrated_operations_application',
    load_order=900,
    source_directory=_APPLICATION_ROOT,
    filename_ordered=True,
)


def build_application_composition(
    *,
    tool_manifest_resolution: ToolManifestResolution,
    manager: AdaManagerSurfaceComposition | None = None,
    surface_registry: AdaSurfaceRegistry | None = None,
) -> IntegratedOperationsApplicationComposition:
    resolved = resolve_ada_surface(
        baseline_manifest=INTEGRATED_OPERATIONS_MANIFEST,
        configuration=tool_manifest_resolution,
        registry=surface_registry or create_operational_surface_registry(),
    )
    return IntegratedOperationsApplicationComposition(
        configuration_resolution=resolved.configuration,
        operational=resolved.surface,
        manager=manager,
    )


def create_operational_surface_registry() -> AdaSurfaceRegistry:
    return AdaSurfaceRegistry((IntegratedOperationsSurfaceAdapter(),))


def build_web_definition(
    *,
    metadata: ApplicationMetadata,
    deployment_modules: Sequence[WebModule],
    composition: IntegratedOperationsApplicationComposition,
    flask_config: Mapping[str, object] | None = None,
) -> WebApplicationDefinition:
    modules = [
        *deployment_modules,
        *composition.operational.modules,
        create_ada_navigation_module(),
    ]
    if composition.manager is not None:
        modules.extend(composition.manager.web_modules)
    modules.append(create_unified_presentation_module(composition))
    return WebApplicationDefinition(
        import_name='integrated_operations',
        metadata=metadata,
        publications_root=Path.cwd() / '.runtime' / 'assets',
        layout=partial(build_application_layout, composition=composition),
        modules=tuple(modules),
        page_packages=('integrated_operations.pages',),
        asset_layers=(APPLICATION_ASSET_LAYER,),
        index=IndexPageDefinition(language='es'),
        flask_config=dict(flask_config or {}),
    )
