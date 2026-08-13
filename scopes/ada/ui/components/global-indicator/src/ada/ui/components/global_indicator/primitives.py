from __future__ import annotations

import re

from dash import html
from dash.development.base_component import Component

from ada.ui.framework.core import DisplayStatus, DisplayValue, resolve_status_visual

from .models import (
    GlobalIndicatorMeasurementState,
    GlobalIndicatorStyle,
    IndicatorColorClass,
)

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
    measurements: tuple[GlobalIndicatorMeasurementState, ...],
    style: GlobalIndicatorStyle,
) -> tuple[Component, ...]:
    table_rows: list[Component] = []
    last_measurement: Component | None = None

    for measurement in measurements:
        if measurement.is_last_measurement:
            last_measurement = _build_last_measurement(
                label_class_name=style.last_measurement_label_class,
                value=measurement.real_value,
                value_class_name=style.last_measurement_value_class,
                color_class=measurement.color_class,
            )
            continue
        table_rows.append(_build_table_row(state=measurement, style=style))

    content: list[Component] = []
    if table_rows:
        content.append(_build_table(rows=table_rows))
    if last_measurement is not None:
        content.append(last_measurement)
    return tuple(content)


def _build_table(*, rows: list[Component]) -> Component:
    return html.Table(
        className='global-indicator__table',
        children=[html.Tbody(children=rows)],
    )


def _build_table_row(
    *,
    state: GlobalIndicatorMeasurementState,
    style: GlobalIndicatorStyle,
) -> Component:
    return html.Tr(
        className='global-indicator__row',
        children=[
            _build_table_value_cell(
                value=DisplayValue.ok(state.temporality),
                value_class_name=(
                    f'global-indicator__value--temporality {style.temporality_class}'
                ),
                is_header=True,
            ),
            _build_table_value_cell(
                value=state.real_value,
                color_class=state.color_class,
                value_class_name=f'global-indicator__value--real {style.real_value_class}',
            ),
            _build_table_separator_cell(class_name=style.plan_value_class),
            _build_table_value_cell(
                value=state.plan_value,
                value_class_name=f'global-indicator__value--plan {style.plan_value_class}',
            ),
        ],
    )


def _build_table_value_cell(
    *,
    value: DisplayValue | None,
    color_class: IndicatorColorClass = None,
    value_class_name: str = '',
    is_header: bool = False,
) -> Component:
    component = html.Th if is_header else html.Td
    attributes = {'scope': 'row'} if is_header else {}
    resolved_value = value or DisplayValue.empty()
    return component(
        className='global-indicator__cell',
        children=[
            html.P(
                className=' '.join(
                    part
                    for part in (
                        'global-indicator__value',
                        value_class_name,
                        _safe_class_names(value=color_class)
                        if resolved_value.status is DisplayStatus.OK
                        else '',
                    )
                    if part
                ),
                children=[_build_display_value(resolved_value)],
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
    value: DisplayValue,
    value_class_name: str,
    color_class: IndicatorColorClass = None,
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
                        _safe_class_names(value=color_class)
                        if value.status is DisplayStatus.OK
                        else '',
                    )
                    if part
                ),
                children=[_build_display_value(value)],
            ),
            html.P(
                className=f'global-indicator__last-measurement-label {label_class_name}',
                children=['Última medición'],
            ),
        ],
    )


def _build_display_value(value: DisplayValue) -> str | Component:
    if value.status is DisplayStatus.OK:
        if isinstance(value.value, Component):
            return value.value
        return str(value.value)

    visual = resolve_status_visual(value.status)
    if visual is None:
        visual = resolve_status_visual(DisplayStatus.ERROR)
    if visual is None:
        return '-'
    return html.Img(
        src=visual.asset_url,
        alt=visual.alt,
        title=visual.title,
        className='ada-status-icon global-indicator__status-icon',
    )


def _safe_class_names(*, value: IndicatorColorClass) -> str:
    if not isinstance(value, str):
        return ''
    tokens = value.split()
    if tokens and all(_CLASS_TOKEN.fullmatch(token) for token in tokens):
        return ' '.join(tokens)
    return ''
