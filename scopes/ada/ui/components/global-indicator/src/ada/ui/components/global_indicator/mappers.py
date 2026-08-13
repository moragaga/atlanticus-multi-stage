from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ada.ui.framework.core import DisplayValue, coerce_display_value

from .definitions import GlobalIndicatorDefinition, GlobalIndicatorMeasurementDefinition
from .models import (
    GlobalIndicatorCollection,
    GlobalIndicatorMeasurementKind,
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
)


def map_global_indicator_measurement(
    *,
    definition: GlobalIndicatorMeasurementDefinition,
    default_key: str,
    kpis: Mapping[str, Any],
) -> GlobalIndicatorMeasurementState:
    is_last_measurement = definition.kind is GlobalIndicatorMeasurementKind.LAST_MEASUREMENT
    real_key = definition.real_kpi_key(default_key=default_key)
    plan_key = definition.plan_kpi_key(default_key=default_key)
    color_key = definition.color_kpi_key(default_key=default_key)
    return GlobalIndicatorMeasurementState(
        real_value=_mapped_value(kpis, real_key),
        color_class=_mapped_color(kpis, color_key),
        temporality=None if is_last_measurement else definition.temporality_label,
        plan_value=None if is_last_measurement else _mapped_value(kpis, plan_key),
        kind=definition.kind,
    )


def map_global_indicator_state(
    *,
    definition: GlobalIndicatorDefinition,
    kpis: Mapping[str, Any],
) -> GlobalIndicatorState:
    return GlobalIndicatorState.from_iterable(
        key=definition.key,
        label=definition.label,
        unit=definition.unit,
        definition_key=definition.definition_key,
        style=definition.style,
        measurements=(
            map_global_indicator_measurement(
                definition=measurement,
                default_key=definition.key,
                kpis=kpis,
            )
            for measurement in definition.measurements
        ),
    )


def map_global_indicator_collection(
    *,
    definitions: tuple[GlobalIndicatorDefinition, ...],
    kpis: Mapping[str, Any],
) -> GlobalIndicatorCollection:
    return GlobalIndicatorCollection.from_iterable(
        map_global_indicator_state(definition=definition, kpis=kpis) for definition in definitions
    )


def _mapped_value(values: Mapping[str, Any], key: str) -> DisplayValue:
    if key not in values:
        return DisplayValue.not_mapped()
    return coerce_display_value(values[key])


def _mapped_color(values: Mapping[str, Any], key: str) -> Any:
    if key not in values:
        return None
    value = coerce_display_value(values[key])
    return value.value if value.status.value == 'ok' else None
