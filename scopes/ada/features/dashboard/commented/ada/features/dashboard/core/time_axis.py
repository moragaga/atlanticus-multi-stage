# Espejo pedagógico en español; la lógica ejecutable es equivalente al archivo productivo.
from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from types import MappingProxyType
from zoneinfo import ZoneInfo

from .projections import ComponentTimeSeriesSnapshot, TimeSeriesWindowSnapshot

from .errors import TimeAxisError
from .models import TimeAxis, TimeSeriesSettings, TimeSeriesWindow

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class TimeAxisBuilder:
    def __init__(self, settings: TimeSeriesSettings) -> None:
        if not isinstance(settings, TimeSeriesSettings):
            raise TimeAxisError('Time axis requires TimeSeriesSettings')
        self._settings = settings
        self._timezone = ZoneInfo(settings.display_timezone)
        self._step = timedelta(seconds=settings.step_seconds)

    def build(self, window: TimeSeriesWindowSnapshot) -> TimeSeriesWindow:
        if not isinstance(window, TimeSeriesWindowSnapshot):
            raise TimeAxisError('Time axis requires TimeSeriesWindowSnapshot')
        self._validate_alignment(window)
        expected_length = self._expected_length(window)
        self._validate_series_lengths(window, expected_length)
        utc_axis = tuple(window.start_utc + index * self._step for index in range(expected_length))
        local_axis = tuple(value.astimezone(self._timezone) for value in utc_axis)
        labels = self._build_labels(local_axis)
        return TimeSeriesWindow(
            hours=window.hours,
            start_utc=window.start_utc,
            end_utc=window.end_utc,
            step_seconds=self._settings.step_seconds,
            axis=TimeAxis(
                utc=utc_axis,
                local=local_axis,
                labels=labels,
                timezone=self._settings.display_timezone,
            ),
            series=MappingProxyType(dict(window.series)),
        )

    def build_snapshot(
        self,
        snapshot: ComponentTimeSeriesSnapshot,
    ) -> MappingProxyType[int, TimeSeriesWindow]:
        if not isinstance(snapshot, ComponentTimeSeriesSnapshot):
            raise TimeAxisError('Time axis requires ComponentTimeSeriesSnapshot')
        return MappingProxyType({window.hours: self.build(window) for window in snapshot.windows})

    def _validate_alignment(self, window: TimeSeriesWindowSnapshot) -> None:
        for name, value in (('start_utc', window.start_utc), ('end_utc', window.end_utc)):
            elapsed_seconds = int((value - _EPOCH).total_seconds())
            if elapsed_seconds % self._settings.step_seconds:
                raise TimeAxisError(f'Time-series window {name} must align to step_seconds')

    def _expected_length(self, window: TimeSeriesWindowSnapshot) -> int:
        duration_seconds = int((window.end_utc - window.start_utc).total_seconds())
        if duration_seconds % self._settings.step_seconds:
            raise TimeAxisError('Time-series window duration must be divisible by step_seconds')
        return duration_seconds // self._settings.step_seconds

    @staticmethod
    def _validate_series_lengths(window: TimeSeriesWindowSnapshot, expected_length: int) -> None:
        for key, values in window.series.items():
            if len(values) != expected_length:
                raise TimeAxisError(
                    f'Time-series {key!r} length does not match its temporal window'
                )

    @staticmethod
    def _build_labels(axis_local: tuple[datetime, ...]) -> tuple[str, ...]:
        base_labels = tuple(value.strftime('%Y-%m-%d %H:%M:%S') for value in axis_local)
        counts = Counter(base_labels)
        labels: list[str] = []
        for value, label in zip(axis_local, base_labels, strict=True):
            if counts[label] == 1:
                labels.append(label)
                continue
            offset = value.strftime('%z')
            labels.append(f'{label} (UTC{offset[:3]}:{offset[3:]})')
        return tuple(labels)
