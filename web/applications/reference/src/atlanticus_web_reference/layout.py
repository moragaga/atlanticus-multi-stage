from __future__ import annotations

from dash import html, page_container

from atlanticus.web.navigation.api import resolve_navigation_from_services
from atlanticus.web.services import ServiceRegistry


def build_layout(services: ServiceRegistry) -> object:
    navigation = resolve_navigation_from_services(services)
    return html.Div(
        [
            html.Header(
                f'{services.require("reference.application_name", str)} · '
                f'{navigation.user.display_name}',
                className='reference-shell__header',
            ),
            html.Main(page_container, className='reference-shell__content'),
        ],
        className='reference-shell',
    )
