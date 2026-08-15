from __future__ import annotations

from dataclasses import dataclass

from ada.features.dashboard.core.errors import DashboardDefinitionError
from ada.runtime.web import SnapshotChannel


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

    def _id(self, kind: str) -> str:
        return f'ada-dashboard--{self.dashboard_key}--{self.component_key}--{kind}'


@dataclass(frozen=True, slots=True)
class DashboardSubcomponentIds:
    dashboard_key: str
    component_key: str
    section_key: str

    def __post_init__(self) -> None:
        for value, name in (
            (self.dashboard_key, 'Dashboard key'),
            (self.component_key, 'Dashboard component key'),
            (self.section_key, 'Dashboard subcomponent key'),
        ):
            if not isinstance(value, str) or not value.strip():
                raise DashboardDefinitionError(f'{name} cannot be empty')

    @property
    def content(self) -> str:
        return self._id('content')

    @property
    def overlay(self) -> str:
        return self._id('overlay')

    def _id(self, kind: str) -> str:
        return (
            f'ada-dashboard--{self.dashboard_key}--{self.component_key}--{self.section_key}--{kind}'
        )


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
