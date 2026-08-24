from __future__ import annotations

from dash import Input, Output, dcc, html

from ada.ui.shell.navigation import build_ada_navigation_offcanvas_from_services
from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry
from integrated_operations.application.models import IntegratedOperationsApplicationComposition

LOCATION_ID = 'ada-unified-application-location'
SURFACE_HOST_ID = 'ada-unified-application-surface-host'
SURFACE_LOADING_ID = 'ada-unified-application-surface-loading'
_MANAGER_ROUTE_PREFIX = '/manager'


def build_unified_application_layout(
    services: ServiceRegistry,
    *,
    composition: IntegratedOperationsApplicationComposition,
):
    return html.Div(
        [
            dcc.Location(id=LOCATION_ID, refresh=False),
            dcc.Loading(
                html.Div(
                    build_application_surface(
                        services,
                        composition=composition,
                        pathname='/',
                    ),
                    id=SURFACE_HOST_ID,
                    className='ada-unified-application__surface-host',
                ),
                id=SURFACE_LOADING_ID,
                type='circle',
                className='ada-unified-application__loading',
            ),
            build_ada_navigation_offcanvas_from_services(services),
        ],
        className='ada-unified-application',
        **{'data-ada-unified-application': 'true'},
    )


def create_unified_presentation_module(
    composition: IntegratedOperationsApplicationComposition,
) -> WebModule:
    def register_callbacks(app: object, services: ServiceRegistry) -> None:
        @app.callback(
            Output(SURFACE_HOST_ID, 'children'),
            Input(LOCATION_ID, 'pathname'),
        )
        def render_surface(pathname: str | None):
            return build_application_surface(
                services,
                composition=composition,
                pathname=pathname,
            )

    return WebModule(
        name='ada-unified-presentation',
        register_callbacks=register_callbacks,
    )


def build_application_surface(
    services: ServiceRegistry,
    *,
    composition: IntegratedOperationsApplicationComposition,
    pathname: str | None,
):
    if composition.manager is not None and composition.manager.matches(pathname):
        return composition.manager.build(services)
    if _is_manager_route(pathname):
        return _build_manager_unavailable_surface()
    return html.Div(
        composition.operational.build(services),
        className=(
            'ada-unified-application__surface ada-unified-application__surface--operational'
        ),
        **{
            'data-ada-unified-surface': 'operational',
            'data-ada-surface-adapter': composition.operational.adapter_key,
        },
    )


def _build_manager_unavailable_surface():
    return html.Main(
        [
            html.H1('Gestor de configuración'),
            html.P('Configuration Manager is not available in this runtime configuration.'),
            dcc.Link('Volver a la aplicación', href='/'),
        ],
        className=(
            'ada-unified-application__surface ada-unified-application__surface--manager-unavailable'
        ),
        **{'data-ada-unified-surface': 'manager-unavailable'},
    )


def _is_manager_route(pathname: str | None) -> bool:
    if not pathname:
        return False
    return pathname == _MANAGER_ROUTE_PREFIX or pathname.startswith(f'{_MANAGER_ROUTE_PREFIX}/')
