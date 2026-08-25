from __future__ import annotations

import json
from collections.abc import Mapping

from ada.ui.framework.core import DisplayStatus

from .errors import RuntimeKpiUiError
from .models import (
    RuntimeKpiValue,
    RuntimeKpiValueKind,
    RuntimeTimeseriesSnapshot,
    RuntimeTimeseriesWindow,
    require_mapping,
    require_sequence,
)


def normalize_latest_value(store_value: object, *, kpi_key: str) -> RuntimeKpiValue:
    key = _require_key(kpi_key)
    if not isinstance(store_value, Mapping):
        return RuntimeKpiValue(DisplayStatus.INVALID)
    state = store_value.get('state')
    if state == 'unmapped':
        return RuntimeKpiValue(DisplayStatus.NOT_MAPPED)
    if state != 'mapped':
        return RuntimeKpiValue(DisplayStatus.INVALID)
    items = store_value.get('items')
    if not isinstance(items, Mapping):
        return RuntimeKpiValue(DisplayStatus.INVALID)
    if key not in items:
        return RuntimeKpiValue(DisplayStatus.NOT_MAPPED)
    item = items[key]
    if not isinstance(item, Mapping):
        return RuntimeKpiValue(DisplayStatus.INVALID)
    status = item.get('status')
    if status == 'missing':
        return RuntimeKpiValue(DisplayStatus.EMPTY)
    if status == 'error':
        return RuntimeKpiValue(DisplayStatus.ERROR)
    if status != 'ok':
        return RuntimeKpiValue(DisplayStatus.INVALID)
    raw_kind = item.get('value_kind')
    try:
        value_kind = RuntimeKpiValueKind(raw_kind)
    except TypeError, ValueError:
        return RuntimeKpiValue(DisplayStatus.INVALID)
    value = item.get('value')
    if value is None:
        return RuntimeKpiValue(DisplayStatus.INVALID)
    if value_kind is RuntimeKpiValueKind.JSON:
        try:
            value = _decode_json_value(value)
        except RuntimeKpiUiError:
            return RuntimeKpiValue(DisplayStatus.INVALID)
    return RuntimeKpiValue(DisplayStatus.OK, value_kind=value_kind, value=value)


def decode_timeseries_store(store_value: object) -> RuntimeTimeseriesSnapshot | None:
    if not isinstance(store_value, Mapping):
        raise RuntimeKpiUiError('Timeseries store must be a mapping')
    state = store_value.get('state')
    if state == 'unmapped':
        return None
    if state != 'mapped':
        raise RuntimeKpiUiError('Timeseries store state is invalid')
    step_seconds = store_value.get('step_seconds')
    if isinstance(step_seconds, bool) or not isinstance(step_seconds, int) or step_seconds <= 0:
        raise RuntimeKpiUiError('Timeseries store step_seconds must be a positive integer')
    keys_raw = require_sequence(store_value.get('keys'), 'Timeseries keys')
    keys = tuple(_require_key(item) for item in keys_raw)
    windows_raw = require_sequence(store_value.get('windows'), 'Timeseries windows')
    windows: list[RuntimeTimeseriesWindow] = []
    for raw_window in windows_raw:
        window = require_mapping(raw_window, 'Timeseries window')
        window_keys_raw = require_sequence(window.get('keys'), 'Timeseries window keys')
        values_raw = require_sequence(window.get('values'), 'Timeseries window values')
        window_keys = tuple(_require_key(item) for item in window_keys_raw)
        values = tuple(
            tuple(require_sequence(row, 'Timeseries series values')) for row in values_raw
        )
        windows.append(
            RuntimeTimeseriesWindow(
                destination=_require_text(window.get('destination'), 'Timeseries destination'),
                hours=_require_positive_integer(window.get('hours'), 'Timeseries hours'),
                start_utc=_require_text(window.get('start_utc'), 'Timeseries start_utc'),
                end_utc=_require_text(window.get('end_utc'), 'Timeseries end_utc'),
                keys=window_keys,
                values=values,
            )
        )
    return RuntimeTimeseriesSnapshot(
        step_seconds=step_seconds,
        keys=keys,
        windows=tuple(windows),
    )


def _decode_json_value(value: object) -> object:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as error:
            raise RuntimeKpiUiError('Runtime KPI JSON value is invalid') from error
    if isinstance(value, Mapping | list | tuple | int | float | bool):
        try:
            json.dumps(value)
        except TypeError as error:
            raise RuntimeKpiUiError('Runtime KPI JSON value is invalid') from error
        return value
    raise RuntimeKpiUiError('Runtime KPI JSON value is invalid')


def _require_key(value: object) -> str:
    return _require_text(value, 'Runtime KPI key')


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeKpiUiError(f'{label} cannot be empty')
    return value.strip()


def _require_positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RuntimeKpiUiError(f'{label} must be a positive integer')
    return value
