from dash import html

from ada.runtime.component_stores import RuntimeComponentStoreRegistry, RuntimeComponentStoreSpec
from ada.ui.framework.core import DisplayStatus
from ada.ui.runtime_kpi import (
    RuntimeKpiValue,
    RuntimeKpiValueKind,
    build_runtime_component_wrapper,
    render_runtime_kpi_value,
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


def test_wrapper_uses_authoritative_tool_runtime_binding() -> None:
    wrapper = build_runtime_component_wrapper(
        _registry(),
        component_key='component_a',
        content=html.Div('content'),
    )

    assert wrapper.id == 'ada-runtime-component-component_a'
    assert wrapper.to_plotly_json()['props']['data-ada-runtime-component'] == 'component_a'


def test_value_kind_value_is_passed_through_without_formatting() -> None:
    rendered = render_runtime_kpi_value(
        RuntimeKpiValue(
            DisplayStatus.OK,
            value_kind=RuntimeKpiValueKind.VALUE,
            value='66,00',
        )
    )

    assert rendered == '66,00'


def test_json_renderer_runs_only_after_json_was_normalized() -> None:
    rendered = render_runtime_kpi_value(
        RuntimeKpiValue(
            DisplayStatus.OK,
            value_kind=RuntimeKpiValueKind.JSON,
            value={'state': 'RUN'},
        ),
        json_renderer=lambda value: html.Span(value['state']),
    )

    assert isinstance(rendered, html.Span)
    assert rendered.children == 'RUN'


def test_json_without_surface_renderer_fails_closed_to_invalid_visual() -> None:
    rendered = render_runtime_kpi_value(
        RuntimeKpiValue(
            DisplayStatus.OK,
            value_kind=RuntimeKpiValueKind.JSON,
            value={'state': 'RUN'},
        )
    )

    assert isinstance(rendered, html.Img)
    assert rendered.alt == 'Dato inválido'


def test_renderer_exception_fails_closed_to_invalid_visual() -> None:
    def fail(_value):
        raise RuntimeError('boom')

    rendered = render_runtime_kpi_value(
        RuntimeKpiValue(
            DisplayStatus.OK,
            value_kind=RuntimeKpiValueKind.VALUE,
            value='x',
        ),
        value_renderer=fail,
    )

    assert isinstance(rendered, html.Img)
    assert rendered.alt == 'Dato inválido'
