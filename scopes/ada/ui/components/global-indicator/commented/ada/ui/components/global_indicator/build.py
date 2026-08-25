# Este espejo documenta los atributos DOM que exponen identidad y capacidad al runtime/UI.
# La identidad del indicador y de cada measurement queda disponible sin depender del label.
from __future__ import annotations

from dash import html
from dash.development.base_component import Component

from .models import (
    GlobalIndicatorCollection,
    GlobalIndicatorState,
    global_indicator_measurement_capacity,
)
from .primitives import build_indicator_content, build_label


def build_global_indicators(*, collection: GlobalIndicatorCollection) -> Component:
    return html.Div(
        className='global-indicators',
        children=[build_global_indicator(state=indicator) for indicator in collection.indicators],
    )


def build_global_indicator(*, state: GlobalIndicatorState) -> Component:
    attributes = {
        'data-indicator-key': state.key,
        'data-measurement-count': str(len(state.measurements)),
        'data-measurement-capacity': str(global_indicator_measurement_capacity()),
        'data-has-last-measurement': 'true' if state.last_measurement is not None else 'false',
    }
    if state.definition_key is not None:
        attributes['data-definition-key'] = state.definition_key
    return html.Div(
        className='global-indicator',
        **attributes,
        children=[
            build_label(
                label=state.label,
                unit=state.unit,
                class_name=state.style.heading_class,
            ),
            html.Div(
                className='global-indicator__content',
                children=build_indicator_content(
                    measurements=state.measurements,
                    last_measurement=state.last_measurement,
                    style=state.style,
                ),
            ),
        ],
    )
