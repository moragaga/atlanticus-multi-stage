# La aplicación siempre conserva una composición operativa base definida por el código.
# La proyección de Tools, cuando existe y es compatible, personaliza esa composición sin convertirse en requisito de arranque.
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
    # La resolución conserva el estado real de configuración, mientras la composición efectiva siempre existe.
    configuration_resolution, tool_composition = _resolve_tool_composition(
        tool_manifest_resolution
    )
    # Los módulos y callbacks operativos se registran también cuando no existe configuración proyectada.
    snapshot_reader = SharedSnapshotReader(
        IntegratedOperationsSnapshotRepository(tool_composition.dashboard),
        ttl_seconds=1.0,
    )
    modules = [
        *deployment_modules,
        *create_integrated_operations_tool_modules(
            tool_composition,
            snapshot_reader=snapshot_reader,
        ),
    ]
    return WebApplicationDefinition(
        import_name='integrated_operations',
        metadata=metadata,
        publications_root=Path.cwd() / '.runtime' / 'assets',
        layout=partial(
            build_application_layout,
            configuration_resolution=configuration_resolution,
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
) -> tuple[ToolManifestResolution, IntegratedOperationsToolComposition]:
    # Una proyección válida reemplaza declarativamente el baseline para esta ejecución.
    if resolution.ready:
        try:
            composition = build_integrated_operations_composition(resolution.require_manifest())
        except IntegratedOperationsCompositionError:
            # Una configuración explícita incompatible mantiene su estado INVALID y vuelve al baseline seguro.
            return ToolManifestResolution.invalid(), _build_baseline_composition()
        return resolution, composition
    # Ausencia, error de lectura o invalidez previa no eliminan el runtime operativo base.
    return resolution, _build_baseline_composition()


def _build_baseline_composition() -> IntegratedOperationsToolComposition:
    # El manifiesto compilado representa la composición automática del código, no una configuración obligatoria.
    return build_integrated_operations_composition(INTEGRATED_OPERATIONS_MANIFEST)
