# Espejo comentado: repositorio fake con el mismo contrato que luego implementará Cosmos.
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ada.features.dashboard import DashboardDefinition
from ada.runtime.web import SharedSnapshot, SnapshotChannel, SnapshotRepository

_CADENCE_SECONDS = {
    SnapshotChannel.DATA: 2,
    SnapshotChannel.TIME_SERIES: 10,
    SnapshotChannel.STATUS: 2,
}


class IntegratedOperationsSnapshotRepository(SnapshotRepository):
    def __init__(self, definition: DashboardDefinition) -> None:
        self._definition = definition

    def read_revision(self, tool_key: str, channel: SnapshotChannel) -> str:
        self._require_tool(tool_key)
        now = datetime.now(UTC)
        cadence = _CADENCE_SECONDS[channel]
        bucket = int(now.timestamp()) // cadence * cadence
        return datetime.fromtimestamp(bucket, UTC).strftime('%Y%m%d%H%M%S%f')

    def read_snapshot(self, tool_key: str, channel: SnapshotChannel) -> SharedSnapshot:
        revision = self.read_revision(tool_key, channel)
        payload = {
            SnapshotChannel.DATA: self._data_payload,
            SnapshotChannel.TIME_SERIES: self._time_series_payload,
            SnapshotChannel.STATUS: self._status_payload,
        }[channel](revision)
        return SharedSnapshot(revision=revision, payload=payload)

    def _data_payload(self, revision: str) -> dict[str, object]:
        components: dict[str, object] = {}
        for component_index, component in enumerate(self._definition.components):
            projection = component.projection
            if projection is None or not projection.data:
                continue
            components[component.section.key] = {
                child.subcomponent: _value(revision, component_index, child_index)
                for child_index, child in enumerate(component.subcomponents)
                if child.subcomponent is not None
            }
        return {'components': components}

    def _time_series_payload(self, revision: str) -> dict[str, object]:
        settings = self._definition.configuration.time_series
        if settings is None:
            return {'components': {}}
        end_utc = _aligned_revision(revision, settings.step_seconds)
        components: dict[str, object] = {}
        for component_index, component in enumerate(self._definition.components):
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

    def _status_payload(self, _revision: str) -> dict[str, object]:
        return {
            'components': {
                component.section.key: {
                    subcomponent_key: 'ready'
                    for subcomponent_key in component.subcomponent_keys
                }
                for component in self._definition.components
                if component.callback_required
            }
        }

    def _require_tool(self, tool_key: str) -> None:
        if tool_key != self._definition.manifest.tool_key:
            raise KeyError(f'Unknown integrated operations tool: {tool_key!r}')


def _value(revision: str, component_index: int, child_index: int) -> float:
    seed = int(revision[-8:]) + component_index * 29 + child_index * 13
    return round(45 + (seed % 650) / 10, 1)


def _series_values(
    revision: str,
    *,
    count: int,
    component_index: int,
    series_index: int,
) -> list[float | None]:
    seed = int(revision[-8:]) + component_index * 37 + series_index * 19
    base = 70 + (seed % 200) / 10
    values: list[float | None] = []
    for index in range(count):
        if (index + seed) % 181 == 0:
            values.append(None)
            continue
        offset = ((index + seed) % 50 - 25) / 10
        values.append(round(base + offset, 2))
    return values


def _aligned_revision(revision: str, step_seconds: int) -> datetime:
    value = datetime.strptime(revision, '%Y%m%d%H%M%S%f').replace(tzinfo=UTC)
    seconds = int(value.timestamp())
    return datetime.fromtimestamp(seconds // step_seconds * step_seconds, UTC)


def _utc_text(value: datetime) -> str:
    return value.isoformat().replace('+00:00', 'Z')
