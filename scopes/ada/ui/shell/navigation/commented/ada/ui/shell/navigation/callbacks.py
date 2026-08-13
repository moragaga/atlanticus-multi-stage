# Espejo comentado: callbacks visuales ejecutados en el navegador.
from __future__ import annotations

from dash import MATCH, Dash, Input, Output, State

from ada.ui.shell.navigation.ids import AdaNavigationIds
from atlanticus.web.services import ServiceRegistry


def register_ada_navigation_callbacks(app: Dash, _services: ServiceRegistry) -> None:
    app.clientside_callback(
        '''
        function(_mobileClicks, _desktopClicks, isOpen) {
            return !Boolean(isOpen);
        }
        ''',
        Output(AdaNavigationIds.HEADER_OFFCANVAS, 'is_open'),
        Input(AdaNavigationIds.HEADER_MOBILE_TOGGLE, 'n_clicks'),
        Input(AdaNavigationIds.HEADER_DESKTOP_TOGGLE, 'n_clicks'),
        State(AdaNavigationIds.HEADER_OFFCANVAS, 'is_open'),
        prevent_initial_call=True,
    )

    app.clientside_callback(
        '''
        function(nClicks, isOpen) {
            if (!nClicks) {
                return window.dash_clientside.no_update;
            }
            return !Boolean(isOpen);
        }
        ''',
        Output(
            {
                'type': AdaNavigationIds.NAVIGATION_GROUP_COLLAPSE,
                'group_key': MATCH,
            },
            'is_open',
        ),
        Input(
            {
                'type': AdaNavigationIds.NAVIGATION_GROUP_TOGGLE,
                'group_key': MATCH,
            },
            'n_clicks',
        ),
        State(
            {
                'type': AdaNavigationIds.NAVIGATION_GROUP_COLLAPSE,
                'group_key': MATCH,
            },
            'is_open',
        ),
        prevent_initial_call=True,
    )
