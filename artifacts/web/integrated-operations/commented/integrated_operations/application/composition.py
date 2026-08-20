# Aplicación: compone módulos, abre runtime y controla lifecycle por worker.
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from dash import page_container

from ada.compositions.integrated_operations import create_integrated_operations_tool_modules
from ada.runtime.web import SharedSnapshotReader
from atlanticus.web.assets import AssetLayer
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.models import ApplicationMetadata, WebApplicationDefinition
from atlanticus.web.modules import WebModule

from integrated_operations.runtime.snapshots import IntegratedOperationsSnapshotRepository
from integrated_operations.tool import COMPOSITION

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
    flask_config: Mapping[str, object] | None = None,
) -> WebApplicationDefinition:
    snapshot_reader = SharedSnapshotReader(
        IntegratedOperationsSnapshotRepository(COMPOSITION.dashboard),
        ttl_seconds=1.0,
    )
    return WebApplicationDefinition(
        import_name='integrated_operations',
        metadata=metadata,
        publications_root=Path.cwd() / '.runtime' / 'assets',
        layout=lambda _services: page_container,
        modules=(
            *tuple(deployment_modules),
            *create_integrated_operations_tool_modules(
                COMPOSITION,
                snapshot_reader=snapshot_reader,
            ),
        ),
        page_packages=('integrated_operations.pages',),
        asset_layers=(APPLICATION_ASSET_LAYER,),
        index=IndexPageDefinition(language='es'),
        flask_config=dict(flask_config or {}),
    )
