# Espejo comentado: conserva exactamente la lógica productiva del módulo.
# Los comentarios describen la responsabilidad sin alterar el AST ejecutable.
from __future__ import annotations

from dash import html, page_container

from ada.ui.header import build_ada_header
from ada.ui.navigation import (
    build_ada_navigation_desktop_trigger,
    build_ada_navigation_mobile_trigger,
    build_ada_navigation_offcanvas_from_services,
)
from ada_ui_reference.header import build_reference_header_state
from atlanticus.web.services import ServiceRegistry


def build_layout(services: ServiceRegistry) -> object:
    return html.Div(
        [
            build_ada_header(
                build_reference_header_state(),
                desktop_navigation_trigger=build_ada_navigation_desktop_trigger(),
                mobile_navigation_trigger=build_ada_navigation_mobile_trigger(),
            ),
            build_ada_navigation_offcanvas_from_services(services),
            html.Main(page_container, className='reference-ada__content'),
        ],
        className='reference-ada',
    )
