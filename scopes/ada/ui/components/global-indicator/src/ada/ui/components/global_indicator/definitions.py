from __future__ import annotations

import re
from dataclasses import dataclass, field

from .errors import GlobalIndicatorDefinitionError
from .models import GlobalIndicatorStyle, global_indicator_measurement_capacity

_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


@dataclass(frozen=True, slots=True)
class GlobalIndicatorMeasurementDefinition:
    key: str
    label: str
    source_key: str | None = None

    def __post_init__(self) -> None:
        _require_key(self.key, field_name='measurement key')
        _require_text(self.label, field_name='measurement label')
        if self.source_key is not None:
            _require_key(self.source_key, field_name='source_key')

    def actual_kpi_key(self, *, default_key: str) -> str:
        return f'{self._resolved_source_key(default_key)}_{self.key}_real_inst'

    def plan_kpi_key(self, *, default_key: str) -> str:
        return f'{self._resolved_source_key(default_key)}_{self.key}_plan_inst'

    def color_kpi_key(self, *, default_key: str) -> str:
        return f'{self._resolved_source_key(default_key)}_{self.key}_color_inst'

    def runtime_kpi_keys(self, *, default_key: str) -> tuple[str, str, str]:
        return (
            self.actual_kpi_key(default_key=default_key),
            self.plan_kpi_key(default_key=default_key),
            self.color_kpi_key(default_key=default_key),
        )

    def _resolved_source_key(self, default_key: str) -> str:
        return self.source_key or default_key


@dataclass(frozen=True, slots=True)
class GlobalIndicatorLastMeasurementDefinition:
    key: str = 'latest'
    label: str = 'Última medición'
    source_key: str | None = None

    def __post_init__(self) -> None:
        _require_key(self.key, field_name='last measurement key')
        _require_text(self.label, field_name='last measurement label')
        if self.source_key is not None:
            _require_key(self.source_key, field_name='source_key')

    def actual_kpi_key(self, *, default_key: str) -> str:
        return f'{self._resolved_source_key(default_key)}_{self.key}_real_inst'

    def color_kpi_key(self, *, default_key: str) -> str:
        return f'{self._resolved_source_key(default_key)}_{self.key}_color_inst'

    def runtime_kpi_keys(self, *, default_key: str) -> tuple[str, str]:
        return (
            self.actual_kpi_key(default_key=default_key),
            self.color_kpi_key(default_key=default_key),
        )

    def _resolved_source_key(self, default_key: str) -> str:
        return self.source_key or default_key


@dataclass(frozen=True, slots=True)
class GlobalIndicatorDefinition:
    key: str
    label: str
    unit: str
    measurements: tuple[GlobalIndicatorMeasurementDefinition, ...]
    last_measurement: GlobalIndicatorLastMeasurementDefinition | None = None
    definition_key: str | None = None
    style: GlobalIndicatorStyle = field(default_factory=GlobalIndicatorStyle)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'measurements', tuple(self.measurements))
        _require_key(self.key, field_name='key')
        _require_text(self.label, field_name='label')
        _require_text(self.unit, field_name='unit')
        if self.definition_key is not None:
            _require_key(self.definition_key, field_name='definition_key')
        if not 2 <= len(self.measurements) <= global_indicator_measurement_capacity():
            raise GlobalIndicatorDefinitionError(
                'Global indicator requires two or three measurement definitions'
            )
        keys = [item.key for item in self.measurements]
        if len(keys) != len(set(keys)):
            raise GlobalIndicatorDefinitionError(
                'Global indicator contains duplicate measurement definition keys'
            )
        if self.last_measurement is not None and self.last_measurement.key in set(keys):
            raise GlobalIndicatorDefinitionError(
                'Global indicator last measurement definition key must be unique'
            )

    @property
    def measurement_keys(self) -> tuple[str, ...]:
        return tuple(item.key for item in self.measurements)

    @property
    def all_measurement_keys(self) -> tuple[str, ...]:
        if self.last_measurement is None:
            return self.measurement_keys
        return (*self.measurement_keys, self.last_measurement.key)

    def runtime_kpi_keys(self) -> tuple[str, ...]:
        keys = tuple(
            key
            for measurement in self.measurements
            for key in measurement.runtime_kpi_keys(default_key=self.key)
        )
        if self.last_measurement is None:
            return keys
        return (*keys, *self.last_measurement.runtime_kpi_keys(default_key=self.key))


def _require_text(value: str, *, field_name: str) -> None:
    if not value.strip():
        raise GlobalIndicatorDefinitionError(f'{field_name} cannot be empty')


def _require_key(value: str, *, field_name: str) -> None:
    if not _KEY_PATTERN.fullmatch(value):
        raise GlobalIndicatorDefinitionError(f'Invalid global indicator {field_name}: {value!r}')
