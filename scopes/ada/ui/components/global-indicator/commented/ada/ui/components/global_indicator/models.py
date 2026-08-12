# Espejo comentado: conserva exactamente la lógica productiva del módulo.
# Los comentarios describen la responsabilidad sin alterar el AST ejecutable.
from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import TypeAlias

from dash.development.base_component import Component

from .errors import GlobalIndicatorDefinitionError

IndicatorValue: TypeAlias = str | int | float | Component | None
IndicatorColor: TypeAlias = str | Component | None


@dataclass(frozen=True, slots=True)
class IndicatorData:
    real_value: IndicatorValue
    color_value: IndicatorColor = None
    temporality: str | None = None
    plan_value: IndicatorValue = None
    only_last_measurement: bool = False

    def __post_init__(self) -> None:
        if not self.only_last_measurement and not (self.temporality or '').strip():
            raise GlobalIndicatorDefinitionError(
                'Temporal measurement requires a temporality label'
            )


@dataclass(frozen=True, slots=True)
class IndicatorPropertiesData:
    label: str
    temporality: str
    real_value: str
    plan_value: str
    last_measurement_label: str
    last_measurement_value: str


@dataclass(frozen=True, slots=True)
class GlobalIndicatorData:
    label: str
    unit: str
    properties: IndicatorPropertiesData
    indicators: tuple[IndicatorData, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'indicators', tuple(self.indicators))
        if not self.label.strip():
            raise GlobalIndicatorDefinitionError('Global indicator label cannot be empty')
        if not self.unit.strip():
            raise GlobalIndicatorDefinitionError('Global indicator unit cannot be empty')
        if not self.indicators:
            raise GlobalIndicatorDefinitionError(
                'Global indicator requires at least one measurement'
            )
        if sum(item.only_last_measurement for item in self.indicators) > 1:
            raise GlobalIndicatorDefinitionError(
                'Global indicator supports at most one last measurement'
            )

    @classmethod
    def from_iterable(
        cls,
        *,
        label: str,
        unit: str,
        properties: IndicatorPropertiesData,
        indicators: Iterable[IndicatorData],
    ) -> GlobalIndicatorData:
        return cls(
            label=label,
            unit=unit,
            properties=properties,
            indicators=tuple(indicators),
        )

    def to_component(self) -> Component:
        from .build import build_global_indicator

        return build_global_indicator(model=self)


@dataclass(frozen=True, slots=True)
class GlobalIndicatorsData:
    components: tuple[GlobalIndicatorData, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'components', tuple(self.components))

    @classmethod
    def from_iterable(cls, components: Iterable[GlobalIndicatorData]) -> GlobalIndicatorsData:
        return cls(components=tuple(components))

    def to_component(self) -> Component:
        from .build import build_global_indicators

        return build_global_indicators(model=self)

    def __iter__(self) -> Iterator[GlobalIndicatorData]:
        return iter(self.components)

    def __len__(self) -> int:
        return len(self.components)
