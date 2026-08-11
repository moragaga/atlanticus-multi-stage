# Aplicación de referencia: demuestra el contrato web sin introducir lógica de negocio real.
from __future__ import annotations

from pathlib import Path

from atlanticus.web import (
    ApplicationMetadata,
    IndexPageDefinition,
    WebApplicationDefinition,
    create_web_application,
)
from atlanticus_web_reference.layout import build_layout
from atlanticus_web_reference.modules import create_reference_module


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
        modules=(create_reference_module(),),
        index=IndexPageDefinition(
            language='es',
            runtime_config={
                'reference': True,
            },
        ),
    )


def create_app():
    return create_web_application(build_definition())
