from __future__ import annotations
# Espejo comentado: conserva la misma lógica productiva y documenta su responsabilidad.

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from ada.features.dashboard.core.projections import ComponentProjectionState
from ada.ui.components.state_wrapper import ComponentCover

from ada.features.dashboard.core.definition import DashboardComponentDefinition
from ada.features.dashboard.core.errors import DashboardDefinitionError, DashboardStoreError
from ada.features.dashboard.core.models import (
    DashboardToolConfiguration,
    TimeSeriesWindow,
    build_component_bundle,
)
from ada.features.dashboard.runtime.serialization import (
    decode_component_data_snapshot,
    decode_component_state_snapshot,
    decode_component_time_series_snapshot,
)
from ada.features.dashboard.core.time_axis import TimeAxisBuilder

ComponentRenderErrorHandler = Callable[[str, Exception], None]


class ComponentRenderState(StrEnum):
    WAITING = 'waiting'
    READY = 'ready'
    ERROR = 'error'


@dataclass(frozen=True, slots=True)
class ComponentRenderStatus:
    component_key: str
    states: Mapping[str, ComponentRenderState]

    def __post_init__(self) -> None:
        if not isinstance(self.states, Mapping):
            raise DashboardStoreError('Render status states must be a mapping')
        states = dict(self.states)
        if not all(
            isinstance(key, str) and key and isinstance(state, ComponentRenderState)
            for key, state in states.items()
        ):
            raise DashboardStoreError('Invalid render status state mapping')
        object.__setattr__(self, 'states', MappingProxyType(states))

    def state(self, subcomponent_key: str) -> ComponentRenderState | None:
        return self.states.get(subcomponent_key)


@dataclass(frozen=True, slots=True)
class ComponentRenderResult:
    content: Mapping[str, object] | None
    preserve_content: bool
    status: ComponentRenderStatus


def render_component_from_stores(
    *,
    component: DashboardComponentDefinition,
    configuration: DashboardToolConfiguration,
    data_value: object = None,
    time_series_value: object = None,
    on_error: ComponentRenderErrorHandler | None = None,
) -> ComponentRenderResult:
    component_key = component.section.key
    subcomponent_keys = component.subcomponent_keys
    if component.renderer is None or component.projection is None:
        raise DashboardDefinitionError('Dashboard callback requires renderer and projection')

    projection = component.projection
    if projection.data and data_value is None:
        return _waiting(component_key, subcomponent_keys)
    if projection.time_series and time_series_value is None:
        return _waiting(component_key, subcomponent_keys)

    try:
        data_snapshot = decode_component_data_snapshot(data_value) if projection.data else None
        time_series_snapshot = (
            decode_component_time_series_snapshot(time_series_value)
            if projection.time_series
            else None
        )
        windows: Mapping[int, TimeSeriesWindow] = {}
        if time_series_snapshot is not None:
            _validate_time_series_projection(
                component_key=component_key,
                component=component,
                snapshot=time_series_snapshot,
            )
            settings = configuration.time_series
            if settings is None:
                raise DashboardDefinitionError(
                    'Dashboard time-series callback requires time-series settings'
                )
            windows = TimeAxisBuilder(settings).build_snapshot(time_series_snapshot)
        bundle = build_component_bundle(
            component_key=component_key,
            data_snapshot=data_snapshot,
            time_series_snapshot=time_series_snapshot,
            windows=windows,
        )
        content = _validate_rendered_content(
            component_key=component_key,
            expected=subcomponent_keys,
            value=component.renderer(bundle),
        )
        return ComponentRenderResult(
            content=content,
            preserve_content=False,
            status=_render_status(
                component_key,
                subcomponent_keys,
                ComponentRenderState.READY,
            ),
        )
    except Exception as error:
        _notify_error(on_error, component_key, error)
        return ComponentRenderResult(
            content=None,
            preserve_content=True,
            status=_render_status(
                component_key,
                subcomponent_keys,
                ComponentRenderState.ERROR,
            ),
        )


def resolve_subcomponent_cover(
    *,
    component_key: str,
    subcomponent_key: str,
    state_value: object,
    render_status_value: object,
) -> ComponentCover:
    try:
        render_status = decode_render_status(render_status_value, component_key=component_key)
    except DashboardStoreError:
        return ComponentCover.component_error()

    render_state = render_status.state(subcomponent_key)
    if render_state is None or render_state is ComponentRenderState.ERROR:
        return ComponentCover.component_error()

    if state_value is None:
        return ComponentCover.none()

    try:
        state_snapshot = decode_component_state_snapshot(state_value)
    except Exception:
        return ComponentCover.component_error()
    if state_snapshot.component_key != component_key:
        return ComponentCover.component_error()

    state = state_snapshot.state(subcomponent_key)
    if state is None:
        return ComponentCover.component_error()
    if state in {ComponentProjectionState.INVALID, ComponentProjectionState.ERROR}:
        return ComponentCover.component_error()
    if state is ComponentProjectionState.CONSTRUCTION:
        return ComponentCover.construction()
    if state is ComponentProjectionState.UNAVAILABLE:
        return ComponentCover.source_error()
    if render_state is ComponentRenderState.WAITING:
        return ComponentCover.none()
    if state is ComponentProjectionState.STALE:
        return ComponentCover.stale()
    return ComponentCover.none()


def encode_render_status(status: ComponentRenderStatus) -> dict[str, object]:
    if not isinstance(status, ComponentRenderStatus):
        raise DashboardStoreError('Render status store requires ComponentRenderStatus')
    return {
        'component_key': status.component_key,
        'states': {key: state.value for key, state in status.states.items()},
    }


def decode_render_status(value: object, *, component_key: str) -> ComponentRenderStatus:
    if not isinstance(value, Mapping):
        raise DashboardStoreError('Render status store payload must be a mapping')
    stored_component_key = value.get('component_key')
    if stored_component_key != component_key:
        raise DashboardStoreError('Render status component key does not match callback component')
    raw_states = value.get('states')
    if not isinstance(raw_states, Mapping):
        raise DashboardStoreError('Render status states must be a mapping')
    states: dict[str, ComponentRenderState] = {}
    for key, state_value in raw_states.items():
        if not isinstance(key, str) or not key:
            raise DashboardStoreError('Render status subcomponent keys must be non-empty strings')
        if not isinstance(state_value, str):
            raise DashboardStoreError('Render status state must be a string')
        try:
            states[key] = ComponentRenderState(state_value)
        except ValueError as error:
            raise DashboardStoreError(f'Unknown render status state: {state_value!r}') from error
    return ComponentRenderStatus(component_key=component_key, states=states)


def initial_render_status(component: DashboardComponentDefinition) -> dict[str, object]:
    return encode_render_status(
        _render_status(
            component.section.key,
            component.subcomponent_keys,
            ComponentRenderState.WAITING,
        )
    )


def _waiting(
    component_key: str,
    subcomponent_keys: tuple[str, ...],
) -> ComponentRenderResult:
    return ComponentRenderResult(
        content=None,
        preserve_content=True,
        status=_render_status(
            component_key,
            subcomponent_keys,
            ComponentRenderState.WAITING,
        ),
    )


def _render_status(
    component_key: str,
    subcomponent_keys: tuple[str, ...],
    state: ComponentRenderState,
) -> ComponentRenderStatus:
    return ComponentRenderStatus(
        component_key=component_key,
        states={key: state for key in subcomponent_keys},
    )


def _validate_rendered_content(
    *,
    component_key: str,
    expected: tuple[str, ...],
    value: object,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise DashboardStoreError(
            f'Dashboard renderer for {component_key!r} must return a subcomponent mapping'
        )
    content = dict(value)
    keys = set(content)
    expected_keys = set(expected)
    missing = sorted(expected_keys - keys)
    unexpected = sorted(keys - expected_keys)
    if missing:
        raise DashboardStoreError(
            f'Dashboard renderer for {component_key!r} is missing subcomponent: {missing[0]!r}'
        )
    if unexpected:
        raise DashboardStoreError(
            f'Dashboard renderer for {component_key!r} returned unknown subcomponent: '
            f'{unexpected[0]!r}'
        )
    return MappingProxyType(content)


def _validate_time_series_projection(
    *,
    component_key: str,
    component: DashboardComponentDefinition,
    snapshot,
) -> None:
    if snapshot.component_key != component_key:
        raise DashboardStoreError(
            'Time-series snapshot component key does not match callback component'
        )
    projection = component.projection
    if projection is None:
        raise DashboardDefinitionError('Time-series validation requires component projection')
    expected = {item.key: item.hours for item in projection.time_series}
    actual: dict[str, int] = {}
    for window in snapshot.windows:
        for key in window.series:
            if key in actual:
                raise DashboardStoreError(f'Time-series projection contains duplicate key: {key!r}')
            actual[key] = window.hours
    missing = sorted(set(expected) - set(actual))
    if missing:
        raise DashboardStoreError(f'Time-series projection is missing key: {missing[0]!r}')
    unexpected = sorted(set(actual) - set(expected))
    if unexpected:
        raise DashboardStoreError(
            f'Time-series projection contains unexpected key: {unexpected[0]!r}'
        )
    for key, hours in expected.items():
        if actual[key] != hours:
            raise DashboardStoreError(
                f'Time-series projection {key!r} is in {actual[key]}h window, expected {hours}h'
            )


def _notify_error(
    on_error: ComponentRenderErrorHandler | None,
    component_key: str,
    error: Exception,
) -> None:
    if on_error is None:
        return
    try:
        on_error(component_key, error)
    except Exception:
        pass
