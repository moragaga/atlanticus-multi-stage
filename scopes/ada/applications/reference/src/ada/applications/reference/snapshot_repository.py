from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta

from ada.features.dashboard import DashboardDefinition
from ada.runtime.web import SharedSnapshot, SnapshotChannel, SnapshotRepository

_CHANNEL_CADENCE_SECONDS = {
    SnapshotChannel.DATA: 12,
    SnapshotChannel.TIME_SERIES: 20,
    SnapshotChannel.STATUS: 5,
}


class ReferenceSnapshotRepository(SnapshotRepository):
    def __init__(
        self,
        definitions: Mapping[str, DashboardDefinition],
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._definitions = dict(definitions)
        self._clock = clock or (lambda: datetime.now(UTC))

    def read_revision(self, tool_key: str, channel: SnapshotChannel) -> str:
        self._definition(tool_key)
        now = _as_utc(self._clock())
        cadence = _CHANNEL_CADENCE_SECONDS[channel]
        bucket = int(now.timestamp()) // cadence * cadence
        return datetime.fromtimestamp(bucket, UTC).strftime('%Y%m%d%H%M%S%f')

    def read_snapshot(self, tool_key: str, channel: SnapshotChannel) -> SharedSnapshot:
        definition = self._definition(tool_key)
        revision = self.read_revision(tool_key, channel)
        if channel is SnapshotChannel.DATA:
            payload = _data_payload(definition, revision)
        elif channel is SnapshotChannel.TIME_SERIES:
            payload = _time_series_payload(definition, revision)
        elif channel is SnapshotChannel.STATUS:
            payload = _status_payload(definition, revision)
        else:
            raise ValueError(f'Unsupported reference snapshot channel: {channel!r}')
        return SharedSnapshot(revision=revision, payload=payload)

    def _definition(self, tool_key: str) -> DashboardDefinition:
        try:
            return self._definitions[tool_key]
        except KeyError as error:
            raise KeyError(f'Unknown reference dashboard tool: {tool_key!r}') from error


def _data_payload(definition: DashboardDefinition, revision: str) -> dict[str, object]:
    components: dict[str, object] = {}
    for index, component in enumerate(definition.components):
        projection = component.projection
        if projection is None or not projection.data:
            continue
        values: dict[str, object] = {}
        children = definition.manifest.children(component.section.key)
        for child_index, child in enumerate(children):
            if child.subcomponent is None:
                continue
            values[child.subcomponent] = _data_value(
                revision,
                component_index=index,
                child_index=child_index,
            )
        if not values:
            values['value'] = _data_value(revision, component_index=index, child_index=0)
        components[component.section.key] = values
    return {'components': components}


def _time_series_payload(definition: DashboardDefinition, revision: str) -> dict[str, object]:
    settings = definition.configuration.time_series
    if settings is None:
        return {'components': {}}
    revision_time = datetime.strptime(revision, '%Y%m%d%H%M%S%f').replace(tzinfo=UTC)
    end_utc = _align_datetime(revision_time, settings.step_seconds)
    components: dict[str, object] = {}
    for component_index, component in enumerate(definition.components):
        projection = component.projection
        if projection is None or not projection.time_series:
            continue
        grouped: dict[int, list[str]] = {}
        for item in projection.time_series:
            grouped.setdefault(item.hours, []).append(item.key)
        windows = []
        for hours, keys in sorted(grouped.items()):
            start_utc = end_utc - timedelta(hours=hours)
            count = hours * 3600 // settings.step_seconds
            windows.append(
                {
                    'hours': hours,
                    'start_utc': _utc_text(start_utc),
                    'end_utc': _utc_text(end_utc),
                    'series': {
                        key: _series_values(
                            revision,
                            count=count,
                            component_index=component_index,
                            series_index=series_index,
                        )
                        for series_index, key in enumerate(keys)
                    },
                }
            )
        components[component.section.key] = {'windows': windows}
    return {'components': components}


def _status_payload(definition: DashboardDefinition, revision: str) -> dict[str, object]:
    components: dict[str, object] = {}
    revision_time = datetime.strptime(revision, '%Y%m%d%H%M%S%f').replace(tzinfo=UTC)
    phase = (int(revision_time.timestamp()) // _CHANNEL_CADENCE_SECONDS[SnapshotChannel.STATUS]) % 4
    active = tuple(component for component in definition.components if component.callback_required)
    stale_target = None
    if active and phase == 2:
        candidate = active[-1]
        if candidate.subcomponent_keys:
            stale_target = (candidate.section.key, candidate.subcomponent_keys[-1])
    for component in active:
        components[component.section.key] = {
            subcomponent_key: (
                'stale' if stale_target == (component.section.key, subcomponent_key) else 'ready'
            )
            for subcomponent_key in component.subcomponent_keys
        }
    return {'components': components}


def _data_value(
    revision: str,
    *,
    component_index: int,
    child_index: int,
) -> float:
    seed = int(revision[-8:]) + component_index * 17 + child_index * 7
    return round(50 + (seed % 500) / 10, 1)


def _series_values(
    revision: str,
    *,
    count: int,
    component_index: int,
    series_index: int,
) -> list[float | None]:
    seed = int(revision[-8:]) + component_index * 31 + series_index * 13
    base = 60 + (seed % 200) / 10
    values: list[float | None] = []
    for index in range(count):
        if (index + seed) % 97 == 0:
            values.append(None)
            continue
        offset = ((index + seed) % 40 - 20) / 10
        values.append(round(base + offset, 2))
    return values


def _align_datetime(value: datetime, step_seconds: int) -> datetime:
    epoch_seconds = int(value.timestamp())
    aligned_seconds = epoch_seconds // step_seconds * step_seconds
    return datetime.fromtimestamp(aligned_seconds, UTC)


def _utc_text(value: datetime) -> str:
    return value.isoformat().replace('+00:00', 'Z')


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('Reference snapshot clock must return timezone-aware datetimes')
    return value.astimezone(UTC)
