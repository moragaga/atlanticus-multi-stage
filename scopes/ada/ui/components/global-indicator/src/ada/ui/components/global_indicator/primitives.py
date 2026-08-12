from __future__ import annotations

import re

from dash import html
from dash.development.base_component import Component

from .models import IndicatorData, IndicatorPropertiesData, IndicatorValue

_CLASS_TOKEN = re.compile(r'^[A-Za-z_][A-Za-z0-9_-]*$')


def build_label(*, label: str, unit: str, class_name: str) -> Component:
    return html.Div(
        className=f'global-indicator__heading {class_name}',
        children=[
            html.P(
                className='global-indicator__label',
                title=label,
                children=[label],
            ),
            html.I(className='global-indicator__icon bi bi-arrow-right-short px-1'),
            html.P(className='global-indicator__unit', children=[unit]),
        ],
    )


def build_indicator_content(
    *,
    indicators: tuple[IndicatorData, ...],
    properties: IndicatorPropertiesData,
) -> tuple[Component, Component | None]:
    last_measurement_component = None
    table_rows: list[Component] = []

    for indicator in indicators:
        if indicator.only_last_measurement:
            last_measurement_component = _build_last_measurement(
                label_class_name=properties.last_measurement_label,
                value=indicator.real_value,
                value_class_name=properties.last_measurement_value,
                color=indicator.color_value,
            )
            continue
        table_rows.append(_build_table_row(model=indicator, properties=properties))

    return _build_table(rows=table_rows), last_measurement_component


def _build_table(*, rows: list[Component]) -> Component:
    return html.Table(
        className='global-indicator__table',
        children=[html.Tbody(children=rows)],
    )


def _build_table_row(*, model: IndicatorData, properties: IndicatorPropertiesData) -> Component:
    return html.Tr(
        className='global-indicator__row',
        children=[
            _build_table_value_cell(
                value=model.temporality,
                value_class_name=(
                    'global-indicator__value--temporality '
                    f'{properties.temporality}'
                ),
                is_header=True,
            ),
            _build_table_value_cell(
                value=model.real_value,
                color=model.color_value,
                value_class_name=f'global-indicator__value--real {properties.real_value}',
            ),
            _build_table_separator_cell(class_name=properties.plan_value),
            _build_table_value_cell(
                value=model.plan_value,
                value_class_name=f'global-indicator__value--plan {properties.plan_value}',
            ),
        ],
    )


def _build_table_value_cell(
    *,
    value: IndicatorValue,
    color: str | Component | None = None,
    value_class_name: str = '',
    is_header: bool = False,
) -> Component:
    component = html.Th if is_header else html.Td
    attributes = {'scope': 'row'} if is_header else {}
    return component(
        className='global-indicator__cell',
        children=[
            html.P(
                className=' '.join(
                    part
                    for part in (
                        'global-indicator__value',
                        value_class_name,
                        _safe_color(color=color),
                    )
                    if part
                ),
                children=[_safe_value(value=value)],
            )
        ],
        **attributes,
    )


def _build_table_separator_cell(*, class_name: str) -> Component:
    return html.Td(
        className='global-indicator__cell',
        children=[
            html.P(
                className=f'global-indicator__separator {class_name}',
                children=['/'],
            )
        ],
    )


def _build_last_measurement(
    *,
    label_class_name: str,
    value: IndicatorValue,
    value_class_name: str,
    color: str | Component | None = None,
) -> Component:
    return html.Div(
        className='global-indicator__last-measurement',
        children=[
            html.P(
                className=' '.join(
                    part
                    for part in (
                        'global-indicator__last-measurement-value',
                        value_class_name,
                        _safe_color(color=color),
                    )
                    if part
                ),
                children=[_safe_value(value=value)],
            ),
            html.P(
                className=f'global-indicator__last-measurement-label {label_class_name}',
                children=['Última medición'],
            ),
        ],
    )


def _safe_value(*, value: IndicatorValue) -> str | Component:
    if isinstance(value, Component):
        return value
    if value is None:
        return '-'
    return str(value)


def _safe_color(*, color: str | Component | None = None) -> str:
    if not isinstance(color, str):
        return ''
    tokens = color.split()
    if tokens and all(_CLASS_TOKEN.fullmatch(token) for token in tokens):
        return ' '.join(tokens)
    return ''
