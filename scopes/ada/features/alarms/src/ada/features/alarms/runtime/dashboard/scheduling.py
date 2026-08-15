from __future__ import annotations

import re
from enum import StrEnum

from ada.features.alarms.core.errors import AlarmDefinitionError

_QUEUE_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


class AlarmVisibilityStrategy(StrEnum):
    QUEUE_IN_QUEUE = 'queue-in-queue'
    PROCESS = 'process'


def alarm_visibility_scope_attributes(
    strategy: AlarmVisibilityStrategy,
    *,
    rotation_interval_ms: int | None = None,
    distributed_interval_ms: int | None = None,
) -> dict[str, str]:
    if not isinstance(strategy, AlarmVisibilityStrategy):
        raise AlarmDefinitionError(f'Invalid alarm visibility strategy: {strategy!r}')
    attributes = {'data-ada-alarm-visibility-strategy': strategy.value}
    if rotation_interval_ms is not None:
        attributes['data-ada-alarm-rotation-interval-ms'] = str(
            _validate_interval(rotation_interval_ms, 'rotation')
        )
    if distributed_interval_ms is not None:
        attributes['data-ada-alarm-distributed-interval-ms'] = str(
            _validate_interval(distributed_interval_ms, 'distributed')
        )
    return attributes


def alarm_queue_lane_attributes(lane_key: str, *, interval_ms: int) -> dict[str, str]:
    if not isinstance(lane_key, str) or not _QUEUE_KEY_PATTERN.fullmatch(lane_key):
        raise AlarmDefinitionError(f'Invalid alarm queue lane key: {lane_key!r}')
    return {
        'data-ada-alarm-queue-lane': lane_key,
        'data-ada-alarm-queue-interval-ms': str(_validate_interval(interval_ms, 'queue')),
    }


def _validate_interval(value: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise AlarmDefinitionError(f'Invalid alarm {label} interval: {value!r}')
    return value
