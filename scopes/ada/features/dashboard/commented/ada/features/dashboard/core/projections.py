from __future__ import annotations
# Espejo comentado: conserva la misma lógica productiva y documenta su responsabilidad.

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from types import MappingProxyType

from ada.runtime.web.errors import RuntimeDefinitionError

_COMPONENT_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
_SUBCOMPONENT_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


class ComponentProjectionState(StrEnum):
    READY = 'ready'
    STALE = 'stale'
    CONSTRUCTION = 'construction'
    UNAVAILABLE = 'unavailable'
    INVALID = 'invalid'
    ERROR = 'error'


@dataclass(frozen=True, slots=True)
class ComponentDataSnapshot:
    component_key: str
    payload: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_component_key(self.component_key)
        object.__setattr__(self, 'payload', _freeze_payload(self.payload))


@dataclass(frozen=True, slots=True)
class TimeSeriesWindowSnapshot:
    hours: int
    start_utc: datetime
    end_utc: datetime
    series: Mapping[str, Sequence[object | None]]

    def __post_init__(self) -> None:
        _require_hours(self.hours)
        start_utc = _as_utc(self.start_utc)
        end_utc = _as_utc(self.end_utc)
        if start_utc.microsecond or end_utc.microsecond:
            raise RuntimeDefinitionError(
                'Time-series window timestamps cannot contain microseconds'
            )
        if end_utc <= start_utc:
            raise RuntimeDefinitionError('Time-series window end_utc must be after start_utc')
        if end_utc - start_utc != timedelta(hours=self.hours):
            raise RuntimeDefinitionError('Time-series window duration must match hours')
        object.__setattr__(self, 'start_utc', start_utc)
        object.__setattr__(self, 'end_utc', end_utc)
        object.__setattr__(self, 'series', _freeze_series(self.series))


@dataclass(frozen=True, slots=True)
class ComponentTimeSeriesSnapshot:
    component_key: str
    windows: tuple[TimeSeriesWindowSnapshot, ...]

    def __post_init__(self) -> None:
        _require_component_key(self.component_key)
        windows = tuple(self.windows)
        if not windows:
            raise RuntimeDefinitionError(
                'Component time-series snapshot requires at least one window'
            )
        if not all(isinstance(window, TimeSeriesWindowSnapshot) for window in windows):
            raise RuntimeDefinitionError('Invalid time-series window')
        hours = [window.hours for window in windows]
        if len(hours) != len(set(hours)):
            raise RuntimeDefinitionError(
                'Component time-series snapshot contains duplicate windows'
            )
        object.__setattr__(self, 'windows', windows)


@dataclass(frozen=True, slots=True)
class ComponentStateSnapshot:
    component_key: str
    states: Mapping[str, ComponentProjectionState]

    def __post_init__(self) -> None:
        _require_component_key(self.component_key)
        if not isinstance(self.states, Mapping):
            raise RuntimeDefinitionError('Component state snapshot states must be a mapping')
        states: dict[str, ComponentProjectionState] = {}
        for subcomponent_key, state in self.states.items():
            _require_subcomponent_key(subcomponent_key)
            if not isinstance(state, ComponentProjectionState):
                raise RuntimeDefinitionError(
                    f'Invalid component projection state: {state!r}'
                )
            states[subcomponent_key] = state
        object.__setattr__(self, 'states', MappingProxyType(states))

    def state(self, subcomponent_key: str) -> ComponentProjectionState | None:
        _require_subcomponent_key(subcomponent_key)
        return self.states.get(subcomponent_key)


def _freeze_payload(payload: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise RuntimeDefinitionError('Component data payload must be a mapping')
    normalized: dict[str, object] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            raise RuntimeDefinitionError('Component data payload keys must be strings')
        if not key:
            raise RuntimeDefinitionError('Component data payload keys cannot be empty')
        normalized[key] = value
    return MappingProxyType(normalized)


def _freeze_series(
    series: Mapping[str, Sequence[object | None]],
) -> Mapping[str, tuple[object | None, ...]]:
    if not isinstance(series, Mapping):
        raise RuntimeDefinitionError('Time-series values must be a mapping')
    if not series:
        raise RuntimeDefinitionError('Time-series window requires at least one series')
    normalized: dict[str, tuple[object | None, ...]] = {}
    for key, values in series.items():
        if not isinstance(key, str) or not key:
            raise RuntimeDefinitionError('Time-series keys must be non-empty strings')
        if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
            raise RuntimeDefinitionError(f'Time-series values for {key!r} must be a sequence')
        normalized[key] = tuple(values)
    return MappingProxyType(normalized)


def _require_component_key(value: str) -> None:
    if not isinstance(value, str) or not _COMPONENT_KEY_PATTERN.fullmatch(value):
        raise RuntimeDefinitionError(f'Invalid component key: {value!r}')


def _require_subcomponent_key(value: str) -> None:
    if not isinstance(value, str) or not _SUBCOMPONENT_KEY_PATTERN.fullmatch(value):
        raise RuntimeDefinitionError(f'Invalid subcomponent key: {value!r}')


def _require_hours(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeDefinitionError('Time-series hours must be an integer')
    if not 1 <= value <= 24:
        raise RuntimeDefinitionError('Time-series hours must be between 1 and 24')


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise RuntimeDefinitionError('Projection timestamps must be timezone-aware')
    return value.astimezone(UTC)
