from __future__ import annotations

from collections.abc import Mapping
from typing import Any

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
    return GlobalIndicatorMeasurementState(
        real_value=kpis.get(definition.real_kpi_key(default_key=default_key)),
        color_class=kpis.get(definition.color_kpi_key(default_key=default_key)),
        temporality=None if is_last_measurement else definition.temporality_label,
        plan_value=(
            None
            if is_last_measurement
            else kpis.get(definition.plan_kpi_key(default_key=default_key))
        ),
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
