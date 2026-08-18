# Espejo comentado: bootstrap web consumiendo las wheels de la composition.
from __future__ import annotations

from pathlib import Path

from dash import page_container

from ada.compositions.integrated_operations import create_integrated_operations_tool_modules
from ada.runtime.web import SharedSnapshotReader
from atlanticus.web.application import create_web_application
from atlanticus.web.assets import AssetLayer
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.models import ApplicationMetadata, WebApplicationDefinition

from .snapshot_repository import IntegratedOperationsSnapshotRepository
from .tool import COMPOSITION


def build_definition() -> WebApplicationDefinition:
    reader = SharedSnapshotReader(
        IntegratedOperationsSnapshotRepository(COMPOSITION.dashboard),
        ttl_seconds=1.0,
    )
    return WebApplicationDefinition(
        import_name='integrated_operations',
        metadata=ApplicationMetadata(
            application_id='ada-integrated-operations',
            display_name='ADA Integrated Operations',
            version='0.1.0',
        ),
        publications_root=Path.cwd() / '.runtime' / 'assets',
        layout=lambda _services: page_container,
        modules=create_integrated_operations_tool_modules(COMPOSITION, snapshot_reader=reader),
        page_packages=('integrated_operations.pages',),
        asset_layers=(
            AssetLayer(
                name='ada_integrated_operations_artifact',
                load_order=900,
                package='integrated_operations',
            ),
        ),
        index=IndexPageDefinition(language='es'),
    )


def create_app():
    return create_web_application(build_definition())
