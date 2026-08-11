from __future__ import annotations

# Compone Navigation antes del módulo de referencia para demostrar la capability transversal.

from pathlib import Path

from atlanticus.web.application import create_web_application
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.models import ApplicationMetadata, WebApplicationDefinition
from atlanticus.web.navigation import create_navigation_module
from atlanticus_web_reference.layout import build_layout
from atlanticus_web_reference.modules import create_reference_module
from atlanticus_web_reference.navigation import build_reference_navigation


def build_definition() -> WebApplicationDefinition:
    return WebApplicationDefinition(
        import_name='atlanticus_web_reference',
        metadata=ApplicationMetadata(
            application_id='atlanticus-web-reference',
            display_name='Atlanticus Web',
            version='0.1.0',
        ),
        publications_root=Path.cwd() / '.runtime' / 'assets',
        layout=build_layout,
        modules=(
            create_navigation_module(build_reference_navigation()),
            create_reference_module(),
        ),
        index=IndexPageDefinition(
            language='es',
            runtime_config={
                'reference': True,
            },
        ),
    )


def create_app():
    return create_web_application(build_definition())
