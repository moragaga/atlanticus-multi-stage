# Espejo comentado de layout.py.
from __future__ import annotations

from dash import html, page_container

from ada.ui.navigation import (
    build_ada_navigation_desktop_trigger,
    build_ada_navigation_mobile_trigger,
    build_ada_navigation_offcanvas_from_services,
)
from atlanticus.web.services import ServiceRegistry


def build_layout(services: ServiceRegistry) -> object:
    return html.Div(
        [
            html.Header(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Strong('ADA', className='reference-ada__brand'),
                                    html.Span(
                                        'Navigation visual contract',
                                        className='reference-ada__subtitle',
                                    ),
                                ],
                                className='reference-ada__identity',
                            ),
                            html.Div(
                                build_ada_navigation_mobile_trigger(),
                                className='app-header-mobile-toggle',
                            ),
                        ],
                        className='dashboard-header-inner reference-ada__header-inner',
                    ),
                    build_ada_navigation_desktop_trigger(),
                ],
                className='dashboard-header-shell reference-ada__header',
            ),
            build_ada_navigation_offcanvas_from_services(services),
            html.Main(page_container, className='reference-ada__content'),
        ],
        className='reference-ada',
    )
