from pathlib import Path

from dash import page_container

from atlanticus.web.application import create_web_application
from atlanticus.web.assets import AssetLayer
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.models import ApplicationMetadata, WebApplicationDefinition


def build_definition() -> WebApplicationDefinition:
    return WebApplicationDefinition(
        import_name='app',
        metadata=ApplicationMetadata(
            application_id='atlanticus-web-build-smoke',
            display_name='Atlanticus Web Build Smoke',
            version='0.1.0',
        ),
        publications_root=Path.cwd() / '.runtime' / 'assets',
        layout=lambda _services: page_container,
        page_packages=('smoke_pages',),
        asset_layers=(
            AssetLayer(
                name='smoke_application',
                load_order=900,
                source_directory=Path.cwd(),
                resource_directory='assets',
                filename_ordered=True,
            ),
        ),
        index=IndexPageDefinition(language='es'),
    )


runtime = create_web_application(build_definition())
app = runtime.server
