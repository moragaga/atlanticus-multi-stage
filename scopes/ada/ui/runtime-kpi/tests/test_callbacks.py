from pathlib import Path

from dash import Dash, html

from ada.runtime.component_stores import RuntimeComponentStoreRegistry, RuntimeComponentStoreSpec
from ada.ui.runtime_kpi import (
    RuntimeLatestOutputBinding,
    register_runtime_latest_callback,
    register_runtime_timeseries_callback,
)


def _registry() -> RuntimeComponentStoreRegistry:
    return RuntimeComponentStoreRegistry(
        tool_key='generic_tool',
        components=(
            RuntimeComponentStoreSpec(
                component_key='component_a',
                wrapper_id='ada-runtime-component-component_a',
                latest_store_id='ada-runtime-kpi-latest-component_a',
                timeseries_store_id='ada-runtime-kpi-timeseries-component_a',
            ),
        ),
    )


def test_latest_ui_block_uses_one_store_input_for_multiple_kpis() -> None:
    app = Dash(__name__)
    app.layout = html.Div([html.Div(id='value-a'), html.Div(id='value-b')])

    register_runtime_latest_callback(
        app,
        registry=_registry(),
        component_key='component_a',
        bindings=(
            RuntimeLatestOutputBinding(output_id='value-a', kpi_key='kpi_a'),
            RuntimeLatestOutputBinding(output_id='value-b', kpi_key='kpi_b'),
        ),
    )

    assert len(app.callback_map) == 1
    callback = next(iter(app.callback_map.values()))
    assert callback['inputs'] == [{'id': 'ada-runtime-kpi-latest-component_a', 'property': 'data'}]


def test_timeseries_ui_block_uses_one_component_timeseries_store_input() -> None:
    app = Dash(__name__)
    app.layout = html.Div(html.Div(id='trend'))

    register_runtime_timeseries_callback(
        app,
        registry=_registry(),
        component_key='component_a',
        output_id='trend',
        renderer=lambda snapshot: html.Div(str(snapshot.step_seconds)),
    )

    assert len(app.callback_map) == 1
    callback = next(iter(app.callback_map.values()))
    assert callback['inputs'] == [
        {'id': 'ada-runtime-kpi-timeseries-component_a', 'property': 'data'}
    ]


def test_callbacks_are_initial_capable_for_unmapped_bootstrap() -> None:
    source = (
        Path(__file__).resolve().parents[1] / 'src' / 'ada' / 'ui' / 'runtime_kpi' / 'callbacks.py'
    ).read_text(encoding='utf-8')

    assert 'prevent_initial_call=True' not in source
