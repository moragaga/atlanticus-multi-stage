# Este módulo compone la aplicación usando únicamente el manifiesto proyectado resuelto al iniciar.
# Si la proyección no está disponible o es incompatible, conserva la aplicación operativa en un estado explícito de configuración.
from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path

from ada.compositions.integrated_operations import (
    IntegratedOperationsCompositionError,
    IntegratedOperationsToolComposition,
    create_integrated_operations_tool_modules,
)
from ada.contracts.tool_manifest import ToolManifestResolution
from ada.runtime.web import SharedSnapshotReader
from atlanticus.web.assets import AssetLayer
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.models import ApplicationMetadata, WebApplicationDefinition
from atlanticus.web.modules import WebModule
from integrated_operations.application.layout import build_application_layout
from integrated_operations.runtime.snapshots import IntegratedOperationsSnapshotRepository
from integrated_operations.tool import build_integrated_operations_composition

_APPLICATION_ROOT = Path(__file__).resolve().parents[1]

APPLICATION_ASSET_LAYER = AssetLayer(
    name='ada_integrated_operations_application',
    load_order=900,
    source_directory=_APPLICATION_ROOT,
    filename_ordered=True,
)


def build_web_definition(
    *,
    metadata: ApplicationMetadata,
    deployment_modules: Sequence[WebModule],
    tool_manifest_resolution: ToolManifestResolution,
    flask_config: Mapping[str, object] | None = None,
) -> WebApplicationDefinition:
    resolution, tool_composition = _resolve_tool_composition(tool_manifest_resolution)
    modules = list(deployment_modules)
    if tool_composition is not None:
        snapshot_reader = SharedSnapshotReader(
            IntegratedOperationsSnapshotRepository(tool_composition.dashboard),
            ttl_seconds=1.0,
        )
        modules.extend(
            create_integrated_operations_tool_modules(
                tool_composition,
                snapshot_reader=snapshot_reader,
            )
        )
    return WebApplicationDefinition(
        import_name='integrated_operations',
        metadata=metadata,
        publications_root=Path.cwd() / '.runtime' / 'assets',
        layout=partial(
            build_application_layout,
            resolution=resolution,
            composition=tool_composition,
        ),
        modules=tuple(modules),
        page_packages=('integrated_operations.pages',),
        asset_layers=(APPLICATION_ASSET_LAYER,),
        index=IndexPageDefinition(language='es'),
        flask_config=dict(flask_config or {}),
    )


def _resolve_tool_composition(
    resolution: ToolManifestResolution,
) -> tuple[ToolManifestResolution, IntegratedOperationsToolComposition | None]:
    if not resolution.ready:
        return resolution, None
    try:
        composition = build_integrated_operations_composition(resolution.require_manifest())
    except IntegratedOperationsCompositionError:
        return ToolManifestResolution.invalid(), None
    return resolution, composition
