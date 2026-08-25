from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from ada.ui.framework.core import DisplayStatus

from .errors import RuntimeKpiUiError


class RuntimeKpiValueKind(StrEnum):
    VALUE = 'value'
    JSON = 'json'


@dataclass(frozen=True, slots=True)
class RuntimeKpiValue:
    status: DisplayStatus
    value_kind: RuntimeKpiValueKind | None = None
    value: object | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, DisplayStatus):
            raise RuntimeKpiUiError('Runtime KPI status is invalid')
        if self.status is DisplayStatus.OK:
            if not isinstance(self.value_kind, RuntimeKpiValueKind):
                raise RuntimeKpiUiError('Ready runtime KPI requires a value kind')
            if self.value is None:
                raise RuntimeKpiUiError('Ready runtime KPI requires a value')
            return
        if self.value_kind is not None or self.value is not None:
            raise RuntimeKpiUiError('Degraded runtime KPI cannot expose a value payload')


@dataclass(frozen=True, slots=True)
class RuntimeTimeseriesWindow:
    destination: str
    hours: int
    start_utc: str
    end_utc: str
    keys: tuple[str, ...]
    values: tuple[tuple[object | None, ...], ...]

    def __post_init__(self) -> None:
        destination = _require_text(self.destination, 'Timeseries destination')
        start_utc = _require_text(self.start_utc, 'Timeseries start_utc')
        end_utc = _require_text(self.end_utc, 'Timeseries end_utc')
        if isinstance(self.hours, bool) or not isinstance(self.hours, int) or self.hours <= 0:
            raise RuntimeKpiUiError('Timeseries hours must be a positive integer')
        keys = tuple(_require_text(key, 'Timeseries key') for key in self.keys)
        values = tuple(tuple(row) for row in self.values)
        if len(keys) != len(values):
            raise RuntimeKpiUiError('Timeseries keys and values must have the same length')
        object.__setattr__(self, 'destination', destination)
        object.__setattr__(self, 'start_utc', start_utc)
        object.__setattr__(self, 'end_utc', end_utc)
        object.__setattr__(self, 'keys', keys)
        object.__setattr__(self, 'values', values)

    def series(self, key: str) -> tuple[object | None, ...]:
        normalized = _require_text(key, 'Timeseries key')
        try:
            index = self.keys.index(normalized)
        except ValueError as error:
            raise RuntimeKpiUiError(f'Unknown timeseries key: {normalized!r}') from error
        return self.values[index]


@dataclass(frozen=True, slots=True)
class RuntimeTimeseriesSnapshot:
    step_seconds: int
    keys: tuple[str, ...]
    windows: tuple[RuntimeTimeseriesWindow, ...]
    _by_hours: Mapping[int, tuple[RuntimeTimeseriesWindow, ...]] | None = None

    def __post_init__(self) -> None:
        if isinstance(self.step_seconds, bool) or not isinstance(self.step_seconds, int):
            raise RuntimeKpiUiError('Timeseries step_seconds must be an integer')
        if self.step_seconds <= 0:
            raise RuntimeKpiUiError('Timeseries step_seconds must be positive')
        keys = tuple(_require_text(key, 'Timeseries key') for key in self.keys)
        windows = tuple(self.windows)
        if not all(isinstance(window, RuntimeTimeseriesWindow) for window in windows):
            raise RuntimeKpiUiError('Timeseries snapshot contains an invalid window')
        by_hours: dict[int, list[RuntimeTimeseriesWindow]] = {}
        for window in windows:
            by_hours.setdefault(window.hours, []).append(window)
        object.__setattr__(self, 'keys', keys)
        object.__setattr__(self, 'windows', windows)
        object.__setattr__(
            self,
            '_by_hours',
            MappingProxyType({hours: tuple(items) for hours, items in by_hours.items()}),
        )

    def windows_for_hours(self, hours: int) -> tuple[RuntimeTimeseriesWindow, ...]:
        if isinstance(hours, bool) or not isinstance(hours, int) or hours <= 0:
            raise RuntimeKpiUiError('Timeseries hours must be a positive integer')
        by_hours = self._by_hours
        if by_hours is None:
            raise RuntimeKpiUiError('Timeseries snapshot is not initialized')
        return by_hours.get(hours, ())


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeKpiUiError(f'{label} cannot be empty')
    return value.strip()


def require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeKpiUiError(f'{label} must be a mapping')
    return value


def require_sequence(value: object, label: str) -> Sequence[object]:
    if isinstance(value, str | bytes | bytearray) or not isinstance(value, Sequence):
        raise RuntimeKpiUiError(f'{label} must be a sequence')
    return value
