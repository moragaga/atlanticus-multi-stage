# Espejo pedagógico en español; la lógica ejecutable es equivalente al archivo productivo.
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import partial

from dash import Dash, Input, Output, State, no_update

from ada.runtime.web import SharedSnapshotReader, SnapshotChannel

from ada.features.dashboard.core.definition import (
    DashboardComponentDefinition,
    DashboardDefinition,
)
from ada.features.dashboard.runtime.distribution import distribute_shared_snapshot
from ada.features.dashboard.core.errors import DashboardStoreError
from .ids import DashboardComponentIds, DashboardPollingIds

DashboardPollingErrorHandler = Callable[[SnapshotChannel, Exception], None]


@dataclass(frozen=True, slots=True)
class DashboardChannelUpdate:
    revision: str
    component_values: Mapping[str, object]


def dashboard_snapshot_channels(definition: DashboardDefinition) -> tuple[SnapshotChannel, ...]:
    active = tuple(component for component in definition.components if component.callback_required)
    channels: list[SnapshotChannel] = []
    if any(component.projection is not None and component.projection.data for component in active):
        channels.append(SnapshotChannel.DATA)
    if any(
        component.projection is not None and component.projection.time_series
        for component in active
    ):
        channels.append(SnapshotChannel.TIME_SERIES)
    if active:
        channels.append(SnapshotChannel.STATUS)
    return tuple(channels)


def register_dashboard_polling_callbacks(
    app: Dash,
    definition: DashboardDefinition,
    reader: SharedSnapshotReader,
    *,
    dashboard_key: str | None = None,
    on_error: DashboardPollingErrorHandler | None = None,
) -> None:
    if definition.polling is None:
        return
    resolved_dashboard_key = dashboard_key or definition.manifest.tool_key
    polling_ids = DashboardPollingIds(resolved_dashboard_key)
    for channel in dashboard_snapshot_channels(definition):
        components = _channel_components(definition, channel)
        if not components:
            continue
        outputs = [Output(polling_ids.revision(channel), 'data')]
        outputs.extend(
            Output(_component_store_id(resolved_dashboard_key, component, channel), 'data')
            for component in components
        )
        app.callback(
            *outputs,
            Input(polling_ids.interval, 'n_intervals'),
            State(polling_ids.revision(channel), 'data'),
            prevent_initial_call=False,
        )(
            partial(
                _poll_callback,
                definition=definition,
                reader=reader,
                channel=channel,
                components=components,
                on_error=on_error,
            )
        )


def read_dashboard_channel_update(
    *,
    definition: DashboardDefinition,
    reader: SharedSnapshotReader,
    channel: SnapshotChannel,
    client_revision: object = None,
) -> DashboardChannelUpdate | None:
    normalized_revision = _client_revision(client_revision)
    snapshot = reader.read(
        definition.manifest.tool_key,
        channel,
        client_revision=normalized_revision,
    )
    if snapshot is None:
        return None
    components = _channel_components(definition, channel)
    values = distribute_shared_snapshot(
        snapshot,
        channel=channel,
        component_keys=tuple(component.section.key for component in components),
    )
    return DashboardChannelUpdate(
        revision=snapshot.revision,
        component_values=values,
    )


def _poll_callback(
    _n_intervals: object,
    client_revision: object,
    *,
    definition: DashboardDefinition,
    reader: SharedSnapshotReader,
    channel: SnapshotChannel,
    components: tuple[DashboardComponentDefinition, ...],
    on_error: DashboardPollingErrorHandler | None,
):
    try:
        update = read_dashboard_channel_update(
            definition=definition,
            reader=reader,
            channel=channel,
            client_revision=client_revision,
        )
    except Exception as error:
        _notify_error(on_error, channel, error)
        return tuple(no_update for _ in range(len(components) + 1))
    if update is None:
        return tuple(no_update for _ in range(len(components) + 1))
    return (
        update.revision,
        *(update.component_values[component.section.key] for component in components),
    )


def _channel_components(
    definition: DashboardDefinition,
    channel: SnapshotChannel,
) -> tuple[DashboardComponentDefinition, ...]:
    active = tuple(component for component in definition.components if component.callback_required)
    if channel is SnapshotChannel.DATA:
        return tuple(
            component
            for component in active
            if component.projection is not None and component.projection.data
        )
    if channel is SnapshotChannel.TIME_SERIES:
        return tuple(
            component
            for component in active
            if component.projection is not None and component.projection.time_series
        )
    if channel is SnapshotChannel.STATUS:
        return active
    raise DashboardStoreError(f'Unsupported dashboard snapshot channel: {channel!r}')


def _component_store_id(
    dashboard_key: str,
    component: DashboardComponentDefinition,
    channel: SnapshotChannel,
) -> str:
    ids = DashboardComponentIds(dashboard_key, component.section.key)
    if channel is SnapshotChannel.DATA:
        return ids.data_store
    if channel is SnapshotChannel.TIME_SERIES:
        return ids.time_series_store
    if channel is SnapshotChannel.STATUS:
        return ids.state_store
    raise DashboardStoreError(f'Unsupported dashboard snapshot channel: {channel!r}')


def _client_revision(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise DashboardStoreError('Dashboard revision store must contain a string')
    return value


def _notify_error(
    on_error: DashboardPollingErrorHandler | None,
    channel: SnapshotChannel,
    error: Exception,
) -> None:
    if on_error is None:
        return
    try:
        on_error(channel, error)
    except Exception:
        pass
