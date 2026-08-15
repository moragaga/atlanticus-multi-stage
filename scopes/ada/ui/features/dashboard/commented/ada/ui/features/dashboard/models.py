# Contratos inmutables del dashboard. El polling sólo declara una cadencia transversal; los canales se derivan del contrato activo.
from __future__ import annotations

import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ada.runtime.web import ComponentDataSnapshot, ComponentTimeSeriesSnapshot

from .errors import DashboardDefinitionError

_COMPONENT_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')




@dataclass(frozen=True, slots=True)
# Cadencia única de comprobación; DATA, TIME_SERIES y STATUS siguen siendo canales independientes.
class DashboardPollingSettings:
    interval_seconds: float

    def __post_init__(self) -> None:
        if isinstance(self.interval_seconds, bool) or not isinstance(
            self.interval_seconds, int | float
        ):
            raise DashboardDefinitionError('Dashboard polling interval_seconds must be numeric')
        value = float(self.interval_seconds)
        if not math.isfinite(value) or value <= 0:
            raise DashboardDefinitionError(
                'Dashboard polling interval_seconds must be greater than zero'
            )
        object.__setattr__(self, 'interval_seconds', value)

    @property
    def interval_milliseconds(self) -> int:
        return max(1, round(self.interval_seconds * 1000))


@dataclass(frozen=True, slots=True)
class TimeSeriesSettings:
    step_seconds: int
    display_timezone: str

    def __post_init__(self) -> None:
        if isinstance(self.step_seconds, bool) or not isinstance(self.step_seconds, int):
            raise DashboardDefinitionError('Time-series step_seconds must be an integer')
        if self.step_seconds <= 0:
            raise DashboardDefinitionError('Time-series step_seconds must be greater than zero')
        if 3600 % self.step_seconds != 0:
            raise DashboardDefinitionError('Time-series step_seconds must divide one hour exactly')
        timezone_name = self.display_timezone.strip()
        if not timezone_name:
            raise DashboardDefinitionError('Time-series display_timezone cannot be empty')
        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as error:
            raise DashboardDefinitionError(
                f'Unknown time-series display_timezone: {timezone_name!r}'
            ) from error
        object.__setattr__(self, 'display_timezone', timezone_name)


@dataclass(frozen=True, slots=True)
class TimeSeriesProjectionDefinition:
    key: str
    hours: int

    def __post_init__(self) -> None:
        if not isinstance(self.key, str) or not self.key:
            raise DashboardDefinitionError('Time-series projection key cannot be empty')
        if isinstance(self.hours, bool) or not isinstance(self.hours, int):
            raise DashboardDefinitionError('Time-series projection hours must be an integer')
        if not 1 <= self.hours <= 24:
            raise DashboardDefinitionError('Time-series projection hours must be between 1 and 24')


@dataclass(frozen=True, slots=True)
class ComponentProjectionDefinition:
    component_key: str
    data: bool = False
    time_series: tuple[TimeSeriesProjectionDefinition, ...] = ()

    def __post_init__(self) -> None:
        _require_component_key(self.component_key)
        if not isinstance(self.data, bool):
            raise DashboardDefinitionError('Component data projection flag must be boolean')
        time_series = tuple(self.time_series)
        if not all(isinstance(item, TimeSeriesProjectionDefinition) for item in time_series):
            raise DashboardDefinitionError(
                'Component time-series projections must use TimeSeriesProjectionDefinition'
            )
        keys = [item.key for item in time_series]
        if len(keys) != len(set(keys)):
            raise DashboardDefinitionError('Component time-series projection keys must be unique')
        if not self.data and not time_series:
            raise DashboardDefinitionError('Component projection requires data or time-series')
        object.__setattr__(self, 'time_series', time_series)


@dataclass(frozen=True, slots=True)
class DashboardToolConfiguration:
    components: tuple[ComponentProjectionDefinition, ...] = ()
    time_series: TimeSeriesSettings | None = None

    def __post_init__(self) -> None:
        components = tuple(self.components)
        if not all(isinstance(item, ComponentProjectionDefinition) for item in components):
            raise DashboardDefinitionError(
                'Dashboard components must use ComponentProjectionDefinition'
            )
        keys = [item.component_key for item in components]
        if len(keys) != len(set(keys)):
            raise DashboardDefinitionError('Dashboard component projections must be unique')
        has_time_series = any(item.time_series for item in components)
        if has_time_series and self.time_series is None:
            raise DashboardDefinitionError(
                'Dashboard time-series projections require time-series settings'
            )
        if not has_time_series and self.time_series is not None:
            raise DashboardDefinitionError(
                'Dashboard time-series settings require at least one time-series projection'
            )
        if self.time_series is not None and not isinstance(self.time_series, TimeSeriesSettings):
            raise DashboardDefinitionError('Invalid dashboard time-series settings')
        object.__setattr__(self, 'components', components)

    def projection(self, component_key: str) -> ComponentProjectionDefinition | None:
        _require_component_key(component_key)
        return next(
            (item for item in self.components if item.component_key == component_key),
            None,
        )


@dataclass(frozen=True, slots=True)
class TimeAxis:
    utc: tuple[datetime, ...]
    local: tuple[datetime, ...]
    labels: tuple[str, ...]
    timezone: str


@dataclass(frozen=True, slots=True)
class TimeSeriesWindow:
    hours: int
    start_utc: datetime
    end_utc: datetime
    step_seconds: int
    axis: TimeAxis
    series: Mapping[str, tuple[object | None, ...]]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'series', MappingProxyType(dict(self.series)))


@dataclass(frozen=True, slots=True)
class ComponentBundle:
    component_key: str
    data: Mapping[str, object] | None = None
    time_series: Mapping[int, TimeSeriesWindow] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_component_key(self.component_key)
        if self.data is not None:
            object.__setattr__(self, 'data', MappingProxyType(dict(self.data)))
        windows = dict(self.time_series)
        if any(not isinstance(hours, int) or not isinstance(window, TimeSeriesWindow) for hours, window in windows.items()):
            raise DashboardDefinitionError('Invalid component time-series bundle')
        if any(hours != window.hours for hours, window in windows.items()):
            raise DashboardDefinitionError('Component time-series window key does not match hours')
        object.__setattr__(self, 'time_series', MappingProxyType(windows))


ComponentRenderer = Callable[[ComponentBundle], object]


@dataclass(frozen=True, slots=True)
class ComponentRendererDefinition:
    component_key: str
    renderer: ComponentRenderer

    def __post_init__(self) -> None:
        _require_component_key(self.component_key)
        if not callable(self.renderer):
            raise DashboardDefinitionError('Component renderer must be callable')


@dataclass(frozen=True, slots=True)
class ComponentRendererRegistry:
    definitions: tuple[ComponentRendererDefinition, ...] = ()

    def __post_init__(self) -> None:
        definitions = tuple(self.definitions)
        if not all(isinstance(item, ComponentRendererDefinition) for item in definitions):
            raise DashboardDefinitionError(
                'Renderer registry entries must use ComponentRendererDefinition'
            )
        keys = [item.component_key for item in definitions]
        if len(keys) != len(set(keys)):
            raise DashboardDefinitionError('Renderer registry contains duplicate component keys')
        object.__setattr__(self, 'definitions', definitions)

    def renderer(self, component_key: str) -> ComponentRenderer | None:
        _require_component_key(component_key)
        definition = next(
            (item for item in self.definitions if item.component_key == component_key),
            None,
        )
        return definition.renderer if definition is not None else None


def build_component_bundle(
    *,
    component_key: str,
    data_snapshot: ComponentDataSnapshot | None = None,
    time_series_snapshot: ComponentTimeSeriesSnapshot | None = None,
    windows: Mapping[int, TimeSeriesWindow] | None = None,
) -> ComponentBundle:
    _require_component_key(component_key)
    if data_snapshot is not None and data_snapshot.component_key != component_key:
        raise DashboardDefinitionError('Data snapshot component key does not match bundle component')
    if time_series_snapshot is not None and time_series_snapshot.component_key != component_key:
        raise DashboardDefinitionError(
            'Time-series snapshot component key does not match bundle component'
        )
    if time_series_snapshot is None and windows:
        raise DashboardDefinitionError('Time-series windows require a time-series snapshot')
    return ComponentBundle(
        component_key=component_key,
        data=data_snapshot.payload if data_snapshot is not None else None,
        time_series=windows or {},
    )


def _require_component_key(value: str) -> None:
    if not isinstance(value, str) or not _COMPONENT_KEY_PATTERN.fullmatch(value):
        raise DashboardDefinitionError(f'Invalid component key: {value!r}')
