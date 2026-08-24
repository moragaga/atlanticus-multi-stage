from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path

from ada.compositions.integrated_operations import (
    IntegratedOperationsCompositionError,
    IntegratedOperationsToolComposition,
    create_integrated_operations_tool_modules,
)
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST, ToolManifestResolution
from ada.runtime.web import SharedSnapshotReader
from ada.ui.shell.navigation import create_ada_navigation_module
from atlanticus.web.assets import AssetLayer
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.models import ApplicationMetadata, WebApplicationDefinition
from atlanticus.web.modules import WebModule
from integrated_operations.application.layout import build_application_layout
from integrated_operations.application.models import (
    IntegratedOperationsApplicationComposition,
    ManagerSurfaceComposition,
)
from integrated_operations.application.presentation import create_unified_presentation_module
from integrated_operations.runtime.snapshots import IntegratedOperationsSnapshotRepository
from integrated_operations.tool import build_integrated_operations_composition

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
    manager: ManagerSurfaceComposition | None = None,
) -> IntegratedOperationsApplicationComposition:
    configuration_resolution, operational = _resolve_tool_composition(tool_manifest_resolution)
    return IntegratedOperationsApplicationComposition(
        configuration_resolution=configuration_resolution,
        operational=operational,
        manager=manager,
    )


def build_web_definition(
    *,
    metadata: ApplicationMetadata,
    deployment_modules: Sequence[WebModule],
    composition: IntegratedOperationsApplicationComposition,
    flask_config: Mapping[str, object] | None = None,
) -> WebApplicationDefinition:
    snapshot_reader = SharedSnapshotReader(
        IntegratedOperationsSnapshotRepository(composition.operational.dashboard),
        ttl_seconds=1.0,
    )
    modules = [
        *deployment_modules,
        *create_integrated_operations_tool_modules(
            composition.operational,
            snapshot_reader=snapshot_reader,
        ),
        create_ada_navigation_module(),
    ]
    if composition.manager is not None:
        modules.extend(
            (
                composition.manager.principal_binding,
                *composition.manager.surface.web_modules,
            )
        )
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


def _resolve_tool_composition(
    resolution: ToolManifestResolution,
) -> tuple[ToolManifestResolution, IntegratedOperationsToolComposition]:
    if resolution.ready:
        try:
            composition = build_integrated_operations_composition(resolution.require_manifest())
        except IntegratedOperationsCompositionError:
            return ToolManifestResolution.invalid(), _build_baseline_composition()
        return resolution, composition
    return resolution, _build_baseline_composition()


def _build_baseline_composition() -> IntegratedOperationsToolComposition:
    return build_integrated_operations_composition(INTEGRATED_OPERATIONS_MANIFEST)
