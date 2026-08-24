from __future__ import annotations

from datetime import date

from dash import Input, Output, State, dcc, html, no_update

from ada.ui.components.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.shell.header import HeaderBrandState, HeaderState, build_ada_header
from ada.ui.shell.navigation import (
    build_ada_navigation_desktop_trigger,
    build_ada_navigation_mobile_trigger,
    build_ada_navigation_offcanvas_from_services,
)
from atlanticus.web.manager.web.ids import REFRESH_BUTTON_ID, REFRESH_SIGNAL_ID
from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry
from integrated_operations.application.models import IntegratedOperationsApplicationComposition

# El host unificado observa la URL una sola vez y decide qué superficie presentar.
LOCATION_ID = 'ada-unified-application-location'
SURFACE_HOST_ID = 'ada-unified-application-surface-host'
SURFACE_LOADING_ID = 'ada-unified-application-surface-loading'
_MANAGER_ROUTE_PREFIX = '/manager'


# La raíz mantiene un único host dinámico; no conserva dos aplicaciones ocultas en paralelo.
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


# Este módulo registra únicamente routing visual y la actualización global del Manager.
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

        if composition.manager is not None:

            @app.callback(
                Output(REFRESH_SIGNAL_ID, 'data'),
                Input(REFRESH_BUTTON_ID, 'n_clicks'),
                State(REFRESH_SIGNAL_ID, 'data'),
                prevent_initial_call=True,
            )
            def request_manager_refresh(clicks: int | None, current: int | None):
                if not isinstance(clicks, int) or isinstance(clicks, bool) or clicks <= 0:
                    return no_update
                return int(current or 0) + 1

    return WebModule(
        name='ada-unified-presentation',
        register_callbacks=register_callbacks,
    )


# La selección por ruta es de presentación; la autorización sigue perteneciendo a Navigation.
def build_application_surface(
    services: ServiceRegistry,
    *,
    composition: IntegratedOperationsApplicationComposition,
    pathname: str | None,
):
    if _is_manager_route(pathname):
        if composition.manager is None:
            return _build_manager_unavailable_surface()
        return _build_manager_surface(services, composition)
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


# Manager reutiliza su surface real y sólo recibe el nuevo marco visual común.
def _build_manager_surface(
    services: ServiceRegistry,
    composition: IntegratedOperationsApplicationComposition,
):
    manager = composition.manager
    if manager is None:
        raise RuntimeError('Manager composition is not available')
    return html.Div(
        [
            _build_manager_header(),
            html.Div(
                manager.surface.layout(services),
                className='ada-unified-application__manager-body',
            ),
        ],
        className=('ada-unified-application__surface ada-unified-application__surface--manager'),
        **{'data-ada-unified-surface': 'manager'},
    )


# El header administrativo reutiliza el contrato ADA y deja identidad/navegación en el menú común.
def _build_manager_header():
    header = build_ada_header(
        HeaderState(
            tool_key='configuration_manager',
            brand=HeaderBrandState(
                resolved_brand=resolve_brand(
                    ATLANTICUS_BRAND_MANIFEST,
                    BrandContext(current_date=date.today()),
                ),
                application_name='ADA',
                tool_name='Gestor de configuración',
            ),
        ),
        desktop_navigation_trigger=build_ada_navigation_desktop_trigger(),
        mobile_navigation_trigger=build_ada_navigation_mobile_trigger(),
    )
    return html.Div(
        [
            header,
            html.Div(
                html.Button(
                    'Actualizar estados',
                    id=REFRESH_BUTTON_ID,
                    className=(
                        'atlanticus-manager__button atlanticus-manager__button--header '
                        'ada-unified-application__manager-refresh'
                    ),
                ),
                className='ada-unified-application__manager-header-actions',
            ),
        ],
        className='ada-unified-application__manager-header',
    )


# La ausencia del Manager es válida y nunca bloquea la operación principal de ADA.
def _build_manager_unavailable_surface():
    return html.Main(
        [
            html.H1('Gestor de configuración'),
            html.P('Configuration Manager is not available in this runtime configuration.'),
            dcc.Link('Volver a Operaciones Integradas', href='/'),
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
