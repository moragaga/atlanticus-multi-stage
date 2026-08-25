from __future__ import annotations

import sys
from datetime import datetime, timedelta

from dash import Dash, dcc, html

from ada.runtime.component_stores import RuntimeComponentStoreRegistry, RuntimeComponentStoreSpec
from ada.ui.runtime_kpi import (
    RuntimeLatestOutputBinding,
    RuntimeTimeseriesSnapshot,
    build_runtime_component_wrapper,
    register_runtime_latest_callback,
    register_runtime_timeseries_callback,
)

REGISTRY = RuntimeComponentStoreRegistry(
    tool_key='generic_process',
    components=(
        RuntimeComponentStoreSpec(
            component_key='component_a',
            wrapper_id='ada-runtime-component-component_a',
            latest_store_id='ada-runtime-kpi-latest-component_a',
            timeseries_store_id='ada-runtime-kpi-timeseries-component_a',
        ),
    ),
)

LATEST_DATA = {
    'state': 'mapped',
    'items': {
        'produccion_total': {
            'status': 'ok',
            'value_kind': 'value',
            'value': '66,00',
        },
        'estado': {
            'status': 'ok',
            'value_kind': 'json',
            'value': '{"label":"RUN","tone":"ready"}',
        },
        'sin_dato': {
            'status': 'missing',
            'value_kind': None,
            'value': None,
        },
        'con_error': {
            'status': 'error',
            'value_kind': 'value',
            'value': None,
        },
    },
}

TIMESERIES_DATA = {
    'state': 'mapped',
    'step_seconds': 120,
    'keys': ['produccion_total'],
    'windows': [
        {
            'destination': 'component_a',
            'hours': 1,
            'start_utc': '2026-08-25T02:24:00Z',
            'end_utc': '2026-08-25T03:24:00Z',
            'keys': ['produccion_total'],
            'values': [[64.2, 64.8, None, 65.4]],
        }
    ],
}


def build_app() -> Dash:
    app = Dash(__name__)
    app.layout = html.Main(
        [
            dcc.Store(
                id=REGISTRY.latest('component_a'),
                data=LATEST_DATA,
                storage_type='memory',
            ),
            dcc.Store(
                id=REGISTRY.timeseries('component_a'),
                data=TIMESERIES_DATA,
                storage_type='memory',
            ),
            build_runtime_component_wrapper(
                REGISTRY,
                component_key='component_a',
                content=[
                    html.H2('Generic Runtime KPI UI POC'),
                    html.Div(['Producción: ', html.Strong(id='poc-production')]),
                    html.Div(['Estado JSON: ', html.Span(id='poc-json')]),
                    html.Div(['Missing: ', html.Span(id='poc-missing')]),
                    html.Div(['Error: ', html.Span(id='poc-error')]),
                    html.Div(id='poc-timeseries'),
                ],
            ),
        ],
        style={'padding': '2rem'},
    )
    register_runtime_latest_callback(
        app,
        registry=REGISTRY,
        component_key='component_a',
        bindings=(
            RuntimeLatestOutputBinding(
                output_id='poc-production',
                kpi_key='produccion_total',
            ),
            RuntimeLatestOutputBinding(
                output_id='poc-json',
                kpi_key='estado',
                json_renderer=lambda value: html.Strong(value['label']),
            ),
            RuntimeLatestOutputBinding(output_id='poc-missing', kpi_key='sin_dato'),
            RuntimeLatestOutputBinding(output_id='poc-error', kpi_key='con_error'),
        ),
    )
    register_runtime_timeseries_callback(
        app,
        registry=REGISTRY,
        component_key='component_a',
        output_id='poc-timeseries',
        renderer=_render_timeseries,
    )
    return app


def _render_timeseries(snapshot: RuntimeTimeseriesSnapshot):
    window = snapshot.windows_for_hours(1)[0]
    values = window.series('produccion_total')
    start = datetime.fromisoformat(window.start_utc.replace('Z', '+00:00'))
    axis = [
        (start + timedelta(seconds=snapshot.step_seconds * index)).isoformat()
        for index in range(len(values))
    ]
    return dcc.Graph(
        figure={
            'data': [
                {
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'x': axis,
                    'y': list(values),
                    'name': 'produccion_total',
                }
            ],
            'layout': {
                'title': 'Timeseries usando step_seconds explícito',
                'showlegend': False,
            },
        },
        config={'displayModeBar': False, 'responsive': True},
    )


if __name__ == '__main__':
    app = build_app()
    if '--check' in sys.argv:
        print('R5 Generic Runtime KPI UI POC:')
        print(f'component wrapper: {REGISTRY.component("component_a").wrapper_id}')
        print(f'latest store: {REGISTRY.latest("component_a")}')
        print(f'timeseries store: {REGISTRY.timeseries("component_a")}')
        print(f'callbacks registered: {len(app.callback_map)}')
    else:
        app.run(debug=True, port=8051)
