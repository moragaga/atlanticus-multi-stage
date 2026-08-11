# La reference app valida el servicio de navegación sin imponer una presentación genérica.
from __future__ import annotations

from dash import html, page_container

from atlanticus.web.navigation import NAVIGATION_SERVICE_KEY, NavigationMenu
from atlanticus.web.services import ServiceRegistry


def build_layout(services: ServiceRegistry) -> object:
    services.require(NAVIGATION_SERVICE_KEY, NavigationMenu)
    return html.Div(
        [
            html.Header(
                services.require('reference.application_name', str),
                className='reference-shell__header',
            ),
            html.Main(page_container, className='reference-shell__content'),
        ],
        className='reference-shell',
    )
