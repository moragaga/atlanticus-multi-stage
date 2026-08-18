# Espejo comentado: bootstrap mínimo de una herramienta portable basada en wheels.
from __future__ import annotations

from pathlib import Path

from dash import page_container

from ada.compositions.process import create_process_tool_modules
from ada.runtime.web import SharedSnapshotReader
from atlanticus.web.application import create_web_application
from atlanticus.web.assets import AssetLayer
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.models import ApplicationMetadata, WebApplicationDefinition

from .snapshot_repository import ProcessBaseSnapshotRepository
from .tool import COMPOSITION


# El artifact actúa como consumidor externo: construye reader, módulos y página sin copiar capabilities.
def build_definition() -> WebApplicationDefinition:
    reader = SharedSnapshotReader(
        ProcessBaseSnapshotRepository(COMPOSITION.dashboard),
        ttl_seconds=1.0,
    )
    return WebApplicationDefinition(
        import_name='process_base',
        metadata=ApplicationMetadata(
            application_id='ada-process-base',
            display_name='ADA Process Base',
            version='0.1.0',
        ),
        publications_root=Path.cwd() / '.runtime' / 'assets',
        layout=lambda _services: page_container,
        modules=create_process_tool_modules(COMPOSITION, snapshot_reader=reader),
        page_packages=('process_base.pages',),
        asset_layers=(
            AssetLayer(
                name='ada_process_base_artifact',
                load_order=900,
                package='process_base',
            ),
        ),
        index=IndexPageDefinition(language='es'),
    )


# WSGI/Dash se construye mediante el contrato normal de atlanticus.web.
def create_app():
    return create_web_application(build_definition())
