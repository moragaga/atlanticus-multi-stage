from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeAlias

from dash.development.base_component import Component

from .errors import GlobalIndicatorDefinitionError

_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
_CLASS_TOKEN = re.compile(r'^[A-Za-z_][A-Za-z0-9_-]*$')

IndicatorValue: TypeAlias = str | int | float | Component | None
IndicatorColorClass: TypeAlias = str | Component | None


class GlobalIndicatorMeasurementKind(StrEnum):
    TEMPORAL = 'temporal'
    LAST_MEASUREMENT = 'last_measurement'


@dataclass(frozen=True, slots=True)
class GlobalIndicatorStyle:
    heading_class: str = 'font-size-gi-300'
    temporality_class: str = 'font-size-gi-200'
    real_value_class: str = 'font-size-gi-100'
    plan_value_class: str = 'font-size-gi-200'
    last_measurement_label_class: str = 'font-size-gi-400'
    last_measurement_value_class: str = 'font-size-gi-300'

    def __post_init__(self) -> None:
        for field_name in (
            'heading_class',
            'temporality_class',
            'real_value_class',
            'plan_value_class',
            'last_measurement_label_class',
            'last_measurement_value_class',
        ):
            _require_class_tokens(getattr(self, field_name), field_name=field_name)


@dataclass(frozen=True, slots=True)
class GlobalIndicatorMeasurementState:
    real_value: IndicatorValue
    temporality: str | None = None
    plan_value: IndicatorValue = None
    color_class: IndicatorColorClass = None
    kind: GlobalIndicatorMeasurementKind = GlobalIndicatorMeasurementKind.TEMPORAL

    def __post_init__(self) -> None:
        if self.kind is GlobalIndicatorMeasurementKind.TEMPORAL:
            _require_text(self.temporality, field_name='temporality')
            return
        if self.temporality is not None:
            raise GlobalIndicatorDefinitionError(
                'Last measurement cannot declare a temporality label'
            )
        if self.plan_value is not None:
            raise GlobalIndicatorDefinitionError('Last measurement cannot declare a plan value')

    @classmethod
    def temporal(
        cls,
        real_value: IndicatorValue,
        *,
        temporality: str,
        plan_value: IndicatorValue = None,
        color_class: IndicatorColorClass = None,
    ) -> GlobalIndicatorMeasurementState:
        return cls(
            real_value=real_value,
            temporality=temporality,
            plan_value=plan_value,
            color_class=color_class,
        )

    @classmethod
    def last_measurement(
        cls,
        real_value: IndicatorValue,
        *,
        color_class: IndicatorColorClass = None,
    ) -> GlobalIndicatorMeasurementState:
        return cls(
            real_value=real_value,
            color_class=color_class,
            kind=GlobalIndicatorMeasurementKind.LAST_MEASUREMENT,
        )

    @property
    def is_last_measurement(self) -> bool:
        return self.kind is GlobalIndicatorMeasurementKind.LAST_MEASUREMENT


@dataclass(frozen=True, slots=True)
class GlobalIndicatorState:
    key: str
    label: str
    unit: str
    measurements: tuple[GlobalIndicatorMeasurementState, ...]
    definition_key: str | None = None
    style: GlobalIndicatorStyle = field(default_factory=GlobalIndicatorStyle)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'measurements', tuple(self.measurements))
        _require_key(self.key, field_name='key')
        _require_text(self.label, field_name='label')
        _require_text(self.unit, field_name='unit')
        if self.definition_key is not None:
            _require_key(self.definition_key, field_name='definition_key')
        if not self.measurements:
            raise GlobalIndicatorDefinitionError(
                'Global indicator requires at least one measurement'
            )
        if sum(item.is_last_measurement for item in self.measurements) > 1:
            raise GlobalIndicatorDefinitionError(
                'Global indicator supports at most one last measurement'
            )
        temporalities = [
            _normalize_label(item.temporality)
            for item in self.measurements
            if item.kind is GlobalIndicatorMeasurementKind.TEMPORAL and item.temporality is not None
        ]
        if len(temporalities) != len(set(temporalities)):
            raise GlobalIndicatorDefinitionError(
                'Global indicator contains duplicate temporal measurements'
            )

    @classmethod
    def from_iterable(
        cls,
        *,
        key: str,
        label: str,
        unit: str,
        measurements: Iterable[GlobalIndicatorMeasurementState],
        definition_key: str | None = None,
        style: GlobalIndicatorStyle | None = None,
    ) -> GlobalIndicatorState:
        return cls(
            key=key,
            label=label,
            unit=unit,
            measurements=tuple(measurements),
            definition_key=definition_key,
            style=style or GlobalIndicatorStyle(),
        )

    def to_component(self) -> Component:
        from .build import build_global_indicator

        return build_global_indicator(state=self)


@dataclass(frozen=True, slots=True)
class GlobalIndicatorCollection:
    indicators: tuple[GlobalIndicatorState, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'indicators', tuple(self.indicators))
        keys = [indicator.key for indicator in self.indicators]
        if len(keys) != len(set(keys)):
            raise GlobalIndicatorDefinitionError(
                'Global indicator collection contains duplicate keys'
            )

    @classmethod
    def from_iterable(
        cls,
        indicators: Iterable[GlobalIndicatorState],
    ) -> GlobalIndicatorCollection:
        return cls(indicators=tuple(indicators))

    def to_component(self) -> Component:
        from .build import build_global_indicators

        return build_global_indicators(collection=self)

    def __iter__(self) -> Iterator[GlobalIndicatorState]:
        return iter(self.indicators)

    def __len__(self) -> int:
        return len(self.indicators)


def _require_key(value: str, *, field_name: str) -> None:
    if not _KEY_PATTERN.fullmatch(value):
        raise GlobalIndicatorDefinitionError(f'Invalid global indicator {field_name}: {value!r}')


def _require_text(value: str | None, *, field_name: str) -> None:
    if value is None or not value.strip():
        raise GlobalIndicatorDefinitionError(f'Global indicator {field_name} cannot be empty')


def _require_class_tokens(value: str, *, field_name: str) -> None:
    tokens = value.split()
    if not tokens or not all(_CLASS_TOKEN.fullmatch(token) for token in tokens):
        raise GlobalIndicatorDefinitionError(
            f'Invalid global indicator CSS classes for {field_name}: {value!r}'
        )


def _normalize_label(value: str) -> str:
    return ''.join(
        letter
        for letter in unicodedata.normalize('NFD', value)
        if unicodedata.category(letter) != 'Mn'
    ).casefold()
