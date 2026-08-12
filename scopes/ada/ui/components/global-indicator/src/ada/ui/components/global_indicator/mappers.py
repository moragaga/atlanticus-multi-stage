from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .definitions import GlobalIndicatorDefinition, IndicatorDefinition
from .models import (
    GlobalIndicatorData,
    GlobalIndicatorsData,
    IndicatorData,
    IndicatorPropertiesData,
)


def map_indicator_data(
    *,
    indicator: IndicatorDefinition,
    kpis: Mapping[str, Any],
) -> IndicatorData:
    return IndicatorData(
        real_value=kpis.get(indicator.real_kpi_key),
        color_value=kpis.get(indicator.color_kpi_key),
        temporality=indicator.temporality_label,
        plan_value=kpis.get(indicator.plan_kpi_key),
        only_last_measurement=indicator.only_last_measurement,
    )


def map_global_indicator_data(
    *,
    definition: GlobalIndicatorDefinition,
    kpis: Mapping[str, Any],
) -> GlobalIndicatorData:
    properties = definition.properties
    return GlobalIndicatorData.from_iterable(
        label=definition.label,
        unit=definition.unit,
        properties=IndicatorPropertiesData(
            label=properties.label,
            temporality=properties.temporality,
            real_value=properties.real_value,
            plan_value=properties.plan_value,
            last_measurement_label=properties.last_measurement_label,
            last_measurement_value=properties.last_measurement_value,
        ),
        indicators=(
            map_indicator_data(indicator=indicator, kpis=kpis)
            for indicator in definition.indicators
        ),
    )


def map_global_indicators_data(
    *,
    definitions: tuple[GlobalIndicatorDefinition, ...],
    kpis: Mapping[str, Any],
) -> GlobalIndicatorsData:
    return GlobalIndicatorsData.from_iterable(
        map_global_indicator_data(definition=definition, kpis=kpis)
        for definition in definitions
    )
