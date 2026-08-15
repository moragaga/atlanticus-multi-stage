# Espejo pedagógico en español; la lógica ejecutable es equivalente al archivo productivo.
from __future__ import annotations

from dataclasses import dataclass

from ada.runtime.web import SnapshotChannel

from ada.features.dashboard.core.errors import DashboardDefinitionError


@dataclass(frozen=True, slots=True)
class DashboardComponentIds:
    dashboard_key: str
    component_key: str

    def __post_init__(self) -> None:
        if not isinstance(self.dashboard_key, str) or not self.dashboard_key.strip():
            raise DashboardDefinitionError('Dashboard key cannot be empty')
        if not isinstance(self.component_key, str) or not self.component_key.strip():
            raise DashboardDefinitionError('Dashboard component key cannot be empty')

    @property
    def data_store(self) -> str:
        return self._id('data')

    @property
    def time_series_store(self) -> str:
        return self._id('time-series')

    @property
    def state_store(self) -> str:
        return self._id('state')

    @property
    def render_status_store(self) -> str:
        return self._id('render-status')

    @property
    def content(self) -> str:
        return self._id('content')

    @property
    def overlay(self) -> str:
        return self._id('overlay')

    @property
    def wrapper(self) -> str:
        return self._id('wrapper')

    def _id(self, kind: str) -> str:
        return f'ada-dashboard--{self.dashboard_key}--{self.component_key}--{kind}'


@dataclass(frozen=True, slots=True)
class DashboardPollingIds:
    dashboard_key: str

    def __post_init__(self) -> None:
        if not isinstance(self.dashboard_key, str) or not self.dashboard_key.strip():
            raise DashboardDefinitionError('Dashboard key cannot be empty')

    @property
    def interval(self) -> str:
        return f'ada-dashboard--{self.dashboard_key}--poll'

    def revision(self, channel: SnapshotChannel) -> str:
        if not isinstance(channel, SnapshotChannel):
            raise DashboardDefinitionError(f'Invalid dashboard snapshot channel: {channel!r}')
        value = channel.value.replace('_', '-')
        return f'ada-dashboard--{self.dashboard_key}--{value}--revision'
