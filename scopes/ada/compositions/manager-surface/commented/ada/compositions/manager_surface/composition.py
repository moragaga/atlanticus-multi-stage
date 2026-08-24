from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from dash import Input, Output, State, html, no_update
from dash.development.base_component import Component

from ada.ui.components.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.shell.header import HeaderBrandState, HeaderState, build_ada_header
from ada.ui.shell.navigation import (
    build_ada_navigation_desktop_trigger,
    build_ada_navigation_mobile_trigger,
)
from atlanticus.web.assets import AssetLayer
from atlanticus.web.manager import ManagerSurface
from atlanticus.web.manager.web.ids import REFRESH_BUTTON_ID, REFRESH_SIGNAL_ID
from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry


# Agrupa la surface Manager, su principal y la presentación ADA sin convertirla en surface operacional.
@dataclass(frozen=True, slots=True)
class AdaManagerSurfaceComposition:
    surface: ManagerSurface
    principal_binding: WebModule
    presentation_module: WebModule
    header_state: HeaderState

    def __post_init__(self) -> None:
        if not self.surface.definition.route_prefix:
            raise ValueError('Embedded ADA Manager surface requires a route prefix')

    @property
    def route_prefix(self) -> str:
        return self.surface.definition.route_prefix

    @property
    def web_modules(self) -> tuple[WebModule, ...]:
        return (
            self.principal_binding,
            *self.surface.web_modules,
            self.presentation_module,
        )

    def matches(self, pathname: str | None) -> bool:
        if not pathname:
            return False
        return pathname == self.route_prefix or pathname.startswith(f'{self.route_prefix}/')

    def build(self, services: ServiceRegistry) -> Component:
        return _build_manager_surface(
            services,
            surface=self.surface,
            header_state=self.header_state,
        )


# Construye el baseline visual administrativo; la configuración del Manager sigue viviendo en sus contratos existentes.
def create_ada_manager_surface_composition(
    *,
    surface: ManagerSurface,
    principal_binding: WebModule,
    application_name: str = 'ADA',
    tool_name: str = 'Gestor de configuración',
) -> AdaManagerSurfaceComposition:
    header_state = HeaderState(
        tool_key='configuration_manager',
        brand=HeaderBrandState(
            resolved_brand=resolve_brand(
                ATLANTICUS_BRAND_MANIFEST,
                BrandContext(current_date=date.today()),
            ),
            application_name=application_name,
            tool_name=tool_name,
        ),
    )
    return AdaManagerSurfaceComposition(
        surface=surface,
        principal_binding=principal_binding,
        presentation_module=_create_manager_presentation_module(),
        header_state=header_state,
    )


# El refresh global pertenece a esta composición, no al host de Operaciones Integradas.
def _create_manager_presentation_module() -> WebModule:
    def register_callbacks(app: object, _services: ServiceRegistry) -> None:
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
        name='ada-manager-surface-presentation',
        asset_layers=(
            AssetLayer(
                name='ada_manager_surface',
                load_order=850,
                package='ada.compositions.manager_surface',
            ),
        ),
        register_callbacks=register_callbacks,
    )


# Monta Header ADA + Body Manager conservando navegación, identidad y workflow existente.
def _build_manager_surface(
    services: ServiceRegistry,
    *,
    surface: ManagerSurface,
    header_state: HeaderState,
) -> Component:
    return html.Div(
        [
            html.Div(
                [
                    build_ada_header(
                        header_state,
                        desktop_navigation_trigger=build_ada_navigation_desktop_trigger(),
                        mobile_navigation_trigger=build_ada_navigation_mobile_trigger(),
                    ),
                    html.Div(
                        html.Button(
                            'Actualizar estados',
                            id=REFRESH_BUTTON_ID,
                            className=(
                                'atlanticus-manager__button '
                                'atlanticus-manager__button--header '
                                'ada-manager-surface__refresh'
                            ),
                        ),
                        className='ada-manager-surface__header-actions',
                    ),
                ],
                className='ada-manager-surface__header',
            ),
            html.Div(
                surface.layout(services),
                className='ada-manager-surface__body',
            ),
        ],
        className='ada-manager-surface',
        **{
            'data-ada-manager-surface': 'true',
            'data-ada-unified-surface': 'manager',
        },
    )
