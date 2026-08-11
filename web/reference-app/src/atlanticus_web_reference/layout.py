from __future__ import annotations

from dash import html, page_container

from atlanticus.web import ServiceRegistry


def build_layout(services: ServiceRegistry) -> object:
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
