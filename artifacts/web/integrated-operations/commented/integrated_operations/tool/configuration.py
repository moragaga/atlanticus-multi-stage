# Tool: contiene la configuración y composición concreta de Operaciones Integradas.
from __future__ import annotations

from functools import partial

from dash import dcc, html

from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from ada.features.dashboard import (
    ComponentBundle,
    ComponentProjectionDefinition,
    ComponentRendererDefinition,
    ComponentRendererRegistry,
    DashboardPollingSettings,
    DashboardToolConfiguration,
    TimeSeriesProjectionDefinition,
    TimeSeriesSettings,
)

_TIME_SERIES = {
    'stockpile_chacay': (('tendencia_alimentado', 5),),
    'molienda': (('molienda', 1),),
    'flotacion': (('colectiva', 1), ('selectiva', 5)),
}


def build_manifest():
    return INTEGRATED_OPERATIONS_MANIFEST


def build_dashboard_configuration() -> DashboardToolConfiguration:
    return DashboardToolConfiguration(
        components=tuple(
            ComponentProjectionDefinition(
                component_key=component_key,
                data=True,
                time_series=tuple(
                    TimeSeriesProjectionDefinition(key=key, hours=hours)
                    for key, hours in _TIME_SERIES.get(component_key, ())
                ),
            )
            for component_key in _component_keys()
        ),
        time_series=TimeSeriesSettings(
            step_seconds=60,
            display_timezone='America/Santiago',
        ),
    )


def build_renderer_registry() -> ComponentRendererRegistry:
    return ComponentRendererRegistry(
        definitions=tuple(
            ComponentRendererDefinition(
                component_key=component_key,
                renderer=partial(_render_component, component_key=component_key),
            )
            for component_key in _component_keys()
        )
    )


def build_polling_settings() -> DashboardPollingSettings:
    return DashboardPollingSettings(interval_seconds=2)


def _component_keys() -> tuple[str, ...]:
    manifest = INTEGRATED_OPERATIONS_MANIFEST
    return tuple(
        component.key
        for scope_key in ('mine', 'plant')
        for component in manifest.children(scope_key)
    )


def _render_component(bundle: ComponentBundle, *, component_key: str):
    values = bundle.data or {}
    return {
        subcomponent: _render_card(
            bundle, subcomponent=subcomponent, value=values.get(subcomponent)
        )
        for subcomponent in _expected_subcomponents(component_key)
    }


def _render_card(
    bundle: ComponentBundle,
    *,
    subcomponent: str,
    value: object,
):
    children = [html.Div(_display_value(value), className='integrated-operations__value')]
    window = next(
        (item for item in bundle.time_series.values() if subcomponent in item.series),
        None,
    )
    if window is not None:
        children.append(
            dcc.Graph(
                figure={
                    'data': [
                        {
                            'type': 'scatter',
                            'mode': 'lines',
                            'x': [item.isoformat() for item in window.axis.utc],
                            'y': list(window.series[subcomponent]),
                            'customdata': list(window.axis.labels),
                            'hovertemplate': '%{customdata}<br>%{y}<extra></extra>',
                        }
                    ],
                    'layout': {
                        'autosize': True,
                        'margin': {'l': 24, 'r': 8, 't': 4, 'b': 18},
                        'showlegend': False,
                        'xaxis': {'showticklabels': False, 'fixedrange': True},
                        'yaxis': {'fixedrange': True},
                    },
                },
                config={'displayModeBar': False, 'responsive': True},
                className='integrated-operations__graph',
                style={'height': '100%', 'minHeight': 0},
            )
        )
    return html.Div(children, className='integrated-operations__card-content')


def _expected_subcomponents(component_key: str) -> tuple[str, ...]:
    return tuple(
        section.subcomponent
        for section in INTEGRATED_OPERATIONS_MANIFEST.children(component_key)
        if section.subcomponent is not None and not section.linked_component_keys
    )


def _display_value(value: object) -> str:
    if value is None:
        return '—'
    if isinstance(value, float):
        return f'{value:.1f}'
    return str(value)
