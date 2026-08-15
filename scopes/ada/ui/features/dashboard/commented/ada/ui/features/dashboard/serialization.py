# Frontera JSON entre snapshots runtime y dcc.Store, preservando None y orden de series.
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import datetime

from ada.runtime.web import (
    ComponentDataSnapshot,
    ComponentProjectionState,
    ComponentStateSnapshot,
    ComponentTimeSeriesSnapshot,
    TimeSeriesWindowSnapshot,
)

from .errors import DashboardStoreError

JsonValue = None | bool | int | float | str | list['JsonValue'] | dict[str, 'JsonValue']


def encode_component_data_snapshot(snapshot: ComponentDataSnapshot) -> dict[str, JsonValue]:
    if not isinstance(snapshot, ComponentDataSnapshot):
        raise DashboardStoreError('Data store requires ComponentDataSnapshot')
    return {
        'component_key': snapshot.component_key,
        'payload': _json_mapping(snapshot.payload),
    }


def decode_component_data_snapshot(value: object) -> ComponentDataSnapshot:
    mapping = _mapping(value, 'Data store payload must be a mapping')
    return ComponentDataSnapshot(
        component_key=_string(mapping, 'component_key'),
        payload=_mapping(mapping.get('payload'), 'Data store snapshot payload must be a mapping'),
    )


def encode_component_time_series_snapshot(
    snapshot: ComponentTimeSeriesSnapshot,
) -> dict[str, JsonValue]:
    if not isinstance(snapshot, ComponentTimeSeriesSnapshot):
        raise DashboardStoreError('Time-series store requires ComponentTimeSeriesSnapshot')
    return {
        'component_key': snapshot.component_key,
        'windows': [
            {
                'hours': window.hours,
                'start_utc': _utc_text(window.start_utc),
                'end_utc': _utc_text(window.end_utc),
                'series': _json_mapping(window.series),
            }
            for window in snapshot.windows
        ],
    }


def decode_component_time_series_snapshot(value: object) -> ComponentTimeSeriesSnapshot:
    mapping = _mapping(value, 'Time-series store payload must be a mapping')
    raw_windows = mapping.get('windows')
    if isinstance(raw_windows, (str, bytes)) or not isinstance(raw_windows, Sequence):
        raise DashboardStoreError('Time-series store windows must be a sequence')
    windows = tuple(_decode_window(item) for item in raw_windows)
    return ComponentTimeSeriesSnapshot(
        component_key=_string(mapping, 'component_key'),
        windows=windows,
    )


def encode_component_state_snapshot(snapshot: ComponentStateSnapshot) -> dict[str, JsonValue]:
    if not isinstance(snapshot, ComponentStateSnapshot):
        raise DashboardStoreError('State store requires ComponentStateSnapshot')
    return {
        'component_key': snapshot.component_key,
        'state': snapshot.state.value,
    }


def decode_component_state_snapshot(value: object) -> ComponentStateSnapshot:
    mapping = _mapping(value, 'State store payload must be a mapping')
    state_value = _string(mapping, 'state')
    try:
        state = ComponentProjectionState(state_value)
    except ValueError as error:
        raise DashboardStoreError(f'Unknown component projection state: {state_value!r}') from error
    return ComponentStateSnapshot(
        component_key=_string(mapping, 'component_key'),
        state=state,
    )


def _decode_window(value: object) -> TimeSeriesWindowSnapshot:
    mapping = _mapping(value, 'Time-series window must be a mapping')
    series = _mapping(mapping.get('series'), 'Time-series window series must be a mapping')
    normalized_series: dict[str, Sequence[object | None]] = {}
    for key, values in series.items():
        if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
            raise DashboardStoreError(f'Time-series values for {key!r} must be a sequence')
        normalized_series[key] = tuple(values)
    return TimeSeriesWindowSnapshot(
        hours=_integer(mapping, 'hours'),
        start_utc=_datetime(mapping, 'start_utc'),
        end_utc=_datetime(mapping, 'end_utc'),
        series=normalized_series,
    )


def _json_mapping(value: Mapping[str, object]) -> dict[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise DashboardStoreError('Dashboard store mapping is invalid')
    result: dict[str, JsonValue] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key:
            raise DashboardStoreError('Dashboard store keys must be non-empty strings')
        result[key] = _json_value(item)
    return result


def _json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DashboardStoreError('Dashboard store numbers must be finite')
        return value
    if isinstance(value, Mapping):
        return _json_mapping(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_value(item) for item in value]
    raise DashboardStoreError(f'Dashboard store value is not JSON-compatible: {type(value).__name__}')


def _mapping(value: object, message: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise DashboardStoreError(message)
    for key in value:
        if not isinstance(key, str):
            raise DashboardStoreError('Dashboard store mapping keys must be strings')
    return value


def _string(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise DashboardStoreError(f'Dashboard store field {key!r} must be a non-empty string')
    return value


def _integer(mapping: Mapping[str, object], key: str) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise DashboardStoreError(f'Dashboard store field {key!r} must be an integer')
    return value


def _datetime(mapping: Mapping[str, object], key: str) -> datetime:
    value = _string(mapping, key)
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise DashboardStoreError(f'Dashboard store field {key!r} must be an ISO datetime') from error


def _utc_text(value: datetime) -> str:
    return value.isoformat().replace('+00:00', 'Z')
