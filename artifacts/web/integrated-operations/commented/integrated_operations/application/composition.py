from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from ada.compositions.manager_surface import AdaManagerSurfaceComposition
from ada.compositions.surface import AdaSurfaceRegistry, resolve_ada_surface
from ada.compositions.web_application import AdaApplicationComposition, build_ada_web_definition
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST, ToolManifestResolution
from atlanticus.web.assets import AssetLayer
from atlanticus.web.models import ApplicationMetadata, WebApplicationDefinition
from atlanticus.web.modules import WebModule
from integrated_operations.surface import IntegratedOperationsSurfaceAdapter

# El artifact concreto conserva únicamente sus assets y decisiones de deployment.
_APPLICATION_ROOT = Path(__file__).resolve().parents[1]
MANAGER_ROUTE_PREFIX = '/manager'

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
) -> AdaApplicationComposition:
    # Integrated Operations decide su baseline y los adapters disponibles en este artifact.
    resolved = resolve_ada_surface(
        baseline_manifest=INTEGRATED_OPERATIONS_MANIFEST,
        configuration=tool_manifest_resolution,
        registry=surface_registry or create_operational_surface_registry(),
    )
    # La base genérica recibe la resolución terminada y no conoce este manifest ni este adapter.
    return AdaApplicationComposition(
        operational_resolution=resolved,
        manager=manager,
        administration_route_prefix=MANAGER_ROUTE_PREFIX,
    )


def create_operational_surface_registry() -> AdaSurfaceRegistry:
    # El registry concreto se compone aquí; la base ADA no mantiene un catálogo global de tools.
    return AdaSurfaceRegistry((IntegratedOperationsSurfaceAdapter(),))


def build_web_definition(
    *,
    metadata: ApplicationMetadata,
    deployment_modules: Sequence[WebModule],
    composition: AdaApplicationComposition,
    flask_config: Mapping[str, object] | None = None,
) -> WebApplicationDefinition:
    # Import name, páginas y CSS concretos siguen perteneciendo al artifact desplegable.
    return build_ada_web_definition(
        import_name='integrated_operations',
        metadata=metadata,
        deployment_modules=deployment_modules,
        composition=composition,
        page_packages=('integrated_operations.pages',),
        asset_layers=(APPLICATION_ASSET_LAYER,),
        flask_config=flask_config,
    )
