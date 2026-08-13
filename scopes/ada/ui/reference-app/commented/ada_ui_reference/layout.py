# Espejo comentado del startup gate de la aplicación de referencia.
from __future__ import annotations

from dash import html, page_container

from ada.ui.core import build_ready_scope, ready_attributes
from ada.ui.header import build_ada_header
from ada.ui.navigation import (
    build_ada_navigation_desktop_trigger,
    build_ada_navigation_mobile_trigger,
    build_ada_navigation_offcanvas_from_services,
)
from ada_ui_reference.header import build_reference_header_state
from atlanticus.web.services import ServiceRegistry


def build_layout(services: ServiceRegistry) -> object:
    content = html.Div(
        [
            build_ada_header(
                build_reference_header_state(services),
                desktop_navigation_trigger=build_ada_navigation_desktop_trigger(),
                mobile_navigation_trigger=build_ada_navigation_mobile_trigger(),
            ),
            html.Div(
                build_ada_navigation_offcanvas_from_services(services),
                **ready_attributes('navigation', ready=True),
            ),
            html.Main(
                page_container,
                className='reference-ada__content',
            ),
        ],
        className='reference-ada',
    )
    return build_ready_scope(
        content=content,
        required=(
            'global-indicators',
            'alarm-management',
            'alarm-status',
            'navigation',
            'page-content',
        ),
    )
