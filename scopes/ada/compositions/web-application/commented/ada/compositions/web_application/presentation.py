from __future__ import annotations

from dash import Input, Output, dcc, html

from ada.ui.shell.navigation import build_ada_navigation_offcanvas_from_services
from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry

from .models import AdaApplicationComposition

# Estos ids pertenecen al único host dinámico de la aplicación ADA.
LOCATION_ID = 'ada-unified-application-location'
SURFACE_HOST_ID = 'ada-unified-application-surface-host'
SURFACE_LOADING_ID = 'ada-unified-application-surface-loading'

# La carcasa visual transversal carga antes que Manager y que los overrides del artifact concreto.
_ADA_APPLICATION_ASSET_LAYER = AssetLayer(
    name='ada_web_application',
    load_order=800,
    package='ada.compositions.web_application',
)


def build_ada_application_layout(
    services: ServiceRegistry,
    *,
    composition: AdaApplicationComposition,
):
    # Location gobierna el slot dinámico sin mantener hosts paralelos ocultos.
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
            # Navigation es única y transversal para Operational y Administration.
            build_ada_navigation_offcanvas_from_services(services),
        ],
        className='ada-unified-application',
        **{'data-ada-unified-application': 'true'},
    )


def create_ada_application_presentation_module(
    composition: AdaApplicationComposition,
) -> WebModule:
    def register_callbacks(app: object, services: ServiceRegistry) -> None:
        @app.callback(
            Output(SURFACE_HOST_ID, 'children'),
            Input(LOCATION_ID, 'pathname'),
        )
        def render_surface(pathname: str | None):
            # Cada cambio de ruta recompone sólo el contenido del host compartido.
            return build_application_surface(
                services,
                composition=composition,
                pathname=pathname,
            )

    return WebModule(
        name='ada-unified-presentation',
        asset_layers=(_ADA_APPLICATION_ASSET_LAYER,),
        register_callbacks=register_callbacks,
    )


def build_application_surface(
    services: ServiceRegistry,
    *,
    composition: AdaApplicationComposition,
    pathname: str | None,
):
    # Manager decide sus rutas profundas mediante su propia composición.
    if composition.manager is not None and composition.manager.matches(pathname):
        return composition.manager.build(services)
    # Si Administration fue configurada pero no está disponible, se conserva una salida controlada.
    if _matches_route(pathname, composition.administration_route_prefix):
        return _build_administration_unavailable_surface()
    # Cualquier otra ruta pertenece a la surface operacional ya resuelta.
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


def _build_administration_unavailable_surface():
    # La ausencia de Manager no invalida el runtime operacional.
    return html.Main(
        [
            html.H1('Gestor de configuración'),
            html.P('Configuration Manager is not available in this runtime configuration.'),
            dcc.Link('Volver a la aplicación', href='/'),
        ],
        className='ada-unified-application__surface ada-unified-application__surface--manager-unavailable',
        **{'data-ada-unified-surface': 'manager-unavailable'},
    )


def _matches_route(pathname: str | None, route_prefix: str | None) -> bool:
    # El host compara un prefijo inyectado y no conoce nombres de rutas concretas.
    if not pathname or not route_prefix:
        return False
    return pathname == route_prefix or pathname.startswith(f'{route_prefix}/')
