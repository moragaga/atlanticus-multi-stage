from __future__ import annotations

from pathlib import Path

from ada.ui.core import create_ada_ui_module
from ada.ui.navigation import create_ada_navigation_module
from ada_ui_reference.layout import build_layout
from ada_ui_reference.module import create_reference_module
from ada_ui_reference.navigation import build_reference_navigation
from atlanticus.web.application import create_web_application
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.models import ApplicationMetadata, WebApplicationDefinition
from atlanticus.web.navigation import create_navigation_module


def build_definition() -> WebApplicationDefinition:
    return WebApplicationDefinition(
        import_name='ada_ui_reference',
        metadata=ApplicationMetadata(
            application_id='ada-ui-reference',
            display_name='ADA UI',
            version='0.1.0',
        ),
        publications_root=Path.cwd() / '.runtime' / 'assets',
        layout=build_layout,
        modules=(
            create_navigation_module(build_reference_navigation()),
            create_ada_ui_module(),
            create_ada_navigation_module(),
            create_reference_module(),
        ),
        index=IndexPageDefinition(language='es'),
    )


def create_app():
    return create_web_application(build_definition())
