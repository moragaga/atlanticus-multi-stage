# Espejo pedagógico en español; la lógica ejecutable es equivalente al archivo productivo.
from __future__ import annotations

from collections.abc import Mapping

from ada.runtime.web import SharedSnapshot, SnapshotChannel

from ada.features.dashboard.core.projections import (
    ComponentDataSnapshot,
    ComponentProjectionState,
    ComponentStateSnapshot,
)

from ada.features.dashboard.core.errors import DashboardStoreError
from .serialization import (
    decode_component_time_series_snapshot,
    encode_component_data_snapshot,
    encode_component_state_snapshot,
    encode_component_time_series_snapshot,
)


def distribute_shared_snapshot(
    snapshot: SharedSnapshot,
    *,
    channel: SnapshotChannel,
    component_keys: tuple[str, ...],
) -> Mapping[str, object]:
    if not isinstance(snapshot, SharedSnapshot):
        raise DashboardStoreError('Dashboard distribution requires SharedSnapshot')
    if not isinstance(channel, SnapshotChannel):
        raise DashboardStoreError(f'Invalid dashboard snapshot channel: {channel!r}')
    components = _components(snapshot)
    result: dict[str, object] = {}
    for component_key in component_keys:
        raw = components.get(component_key, _MISSING)
        if raw is _MISSING:
            result[component_key] = None
            continue
        result[component_key] = _component_value(
            component_key=component_key,
            channel=channel,
            raw=raw,
        )
    return result


def _components(snapshot: SharedSnapshot) -> Mapping[str, object]:
    value = snapshot.payload.get('components')
    if not isinstance(value, Mapping):
        raise DashboardStoreError('Shared dashboard snapshot requires components mapping')
    for key in value:
        if not isinstance(key, str) or not key:
            raise DashboardStoreError('Shared dashboard component keys must be non-empty strings')
    return value


def _component_value(
    *,
    component_key: str,
    channel: SnapshotChannel,
    raw: object,
) -> object:
    if channel is SnapshotChannel.DATA:
        if not isinstance(raw, Mapping):
            raise DashboardStoreError(
                f'Shared data snapshot for component {component_key!r} must be a mapping'
            )
        return encode_component_data_snapshot(
            ComponentDataSnapshot(component_key=component_key, payload=raw)
        )
    if channel is SnapshotChannel.TIME_SERIES:
        if not isinstance(raw, Mapping):
            raise DashboardStoreError(
                f'Shared time-series snapshot for component {component_key!r} must be a mapping'
            )
        value = dict(raw)
        value['component_key'] = component_key
        return encode_component_time_series_snapshot(decode_component_time_series_snapshot(value))
    if channel is SnapshotChannel.STATUS:
        if not isinstance(raw, str):
            raise DashboardStoreError(
                f'Shared status snapshot for component {component_key!r} must be a string'
            )
        try:
            state = ComponentProjectionState(raw)
        except ValueError as error:
            raise DashboardStoreError(
                f'Unknown component projection state for {component_key!r}: {raw!r}'
            ) from error
        return encode_component_state_snapshot(
            ComponentStateSnapshot(component_key=component_key, state=state)
        )
    raise DashboardStoreError(f'Unsupported dashboard snapshot channel: {channel!r}')


_MISSING = object()
