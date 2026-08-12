from __future__ import annotations

from dash import html
from dash.development.base_component import Component

from .models import GlobalIndicatorData, GlobalIndicatorsData
from .primitives import build_indicator_content, build_label


def build_global_indicators(*, model: GlobalIndicatorsData) -> Component:
    return html.Div(
        className='global-indicators',
        children=[build_global_indicator(model=component) for component in model.components],
    )


def build_global_indicator(*, model: GlobalIndicatorData) -> Component:
    return html.Div(
        className='global-indicator',
        children=[
            build_label(
                label=model.label,
                unit=model.unit,
                class_name=model.properties.label,
            ),
            html.Div(
                className='global-indicator__content',
                children=build_indicator_content(
                    indicators=model.indicators,
                    properties=model.properties,
                ),
            ),
        ],
    )
