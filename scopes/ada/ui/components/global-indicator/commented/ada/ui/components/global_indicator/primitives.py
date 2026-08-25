# Este espejo explica la geometría interna estándar del Global Indicator.
# Siempre se renderizan tres slots visuales; los slots vacíos no crean datos ficticios.
# El área de last measurement también se reserva para mantener tamaño uniforme.
from __future__ import annotations

import re

from dash import html
from dash.development.base_component import Component

from ada.ui.framework.core import DisplayStatus, DisplayValue, resolve_status_visual

from .models import (
    GlobalIndicatorLastMeasurementState,
    GlobalIndicatorMeasurementState,
    GlobalIndicatorStyle,
    IndicatorColorClass,
    global_indicator_measurement_capacity,
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
    last_measurement: GlobalIndicatorLastMeasurementState | None,
    style: GlobalIndicatorStyle,
) -> tuple[Component, ...]:
    rows = [_build_table_row(state=measurement, style=style) for measurement in measurements]
    rows.extend(
        _build_empty_table_row()
        for _ in range(global_indicator_measurement_capacity() - len(measurements))
    )
    return (
        _build_table(rows=rows),
        _build_last_measurement_slot(state=last_measurement, style=style),
    )


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
        **{'data-measurement-key': state.key},
        children=[
            _build_table_value_cell(
                value=DisplayValue.ok(state.label),
                value_class_name=(
                    f'global-indicator__value--measurement-label {style.measurement_label_class}'
                ),
                is_header=True,
            ),
            _build_table_value_cell(
                value=state.actual_value,
                color_class=state.color_class,
                value_class_name=f'global-indicator__value--actual {style.actual_value_class}',
            ),
            _build_table_separator_cell(class_name=style.plan_value_class),
            _build_table_value_cell(
                value=state.plan_value,
                value_class_name=f'global-indicator__value--plan {style.plan_value_class}',
            ),
        ],
    )


def _build_empty_table_row() -> Component:
    return html.Tr(
        className='global-indicator__row global-indicator__row--empty',
        **{'aria-hidden': 'true'},
        children=[html.Td(className='global-indicator__cell', colSpan=4)],
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


def _build_last_measurement_slot(
    *,
    state: GlobalIndicatorLastMeasurementState | None,
    style: GlobalIndicatorStyle,
) -> Component:
    if state is None:
        return html.Div(
            className=(
                'global-indicator__last-measurement global-indicator__last-measurement--empty'
            ),
            **{'aria-hidden': 'true'},
        )
    return html.Div(
        className='global-indicator__last-measurement',
        **{'data-measurement-key': state.key},
        children=[
            html.P(
                className=' '.join(
                    part
                    for part in (
                        'global-indicator__last-measurement-value',
                        style.last_measurement_value_class,
                        _safe_class_names(value=state.color_class)
                        if state.actual_value.status is DisplayStatus.OK
                        else '',
                    )
                    if part
                ),
                children=[_build_display_value(state.actual_value)],
            ),
            html.P(
                className=(
                    f'global-indicator__last-measurement-label {style.last_measurement_label_class}'
                ),
                children=[state.label],
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
