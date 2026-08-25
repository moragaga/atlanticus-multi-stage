from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from dash import Input, Output, State, no_update
from dash.exceptions import PreventUpdate

from ada.runtime.delivery_cache import DeliveryChannel, WorkerDeliveryCache

from .distribution import RuntimeChannelUpdatePlan, plan_channel_updates
from .mount import RuntimeDeliveryCollectorMount
from .refresh import (
    build_acquired_refresh_lock,
    build_refresh_signal,
    build_released_refresh_lock,
    is_refresh_lock_expired,
)


def register_runtime_delivery_collector_callbacks(
    app: Any,
    *,
    mount: RuntimeDeliveryCollectorMount,
    worker_cache: WorkerDeliveryCache,
) -> None:
    component_outputs: list[Output] = []
    component_states: list[State] = []
    for component in mount.registry.components:
        component_outputs.extend(
            (
                Output(component.latest_store_id, 'data'),
                Output(component.timeseries_store_id, 'data'),
            )
        )
        component_states.extend(
            (
                State(component.latest_store_id, 'data'),
                State(component.timeseries_store_id, 'data'),
            )
        )

    @app.callback(
        Output(mount.ids.refresh_signal_store_id, 'data'),
        Input(mount.ids.interval_id, 'n_intervals'),
        State(mount.ids.refresh_lock_store_id, 'data'),
    )
    def request_refresh(n_intervals: object, lock_data: object) -> dict[str, object]:
        if n_intervals is None:
            raise PreventUpdate
        lock = lock_data if isinstance(lock_data, Mapping) else {}
        if bool(lock.get('is_running', False)) and not is_refresh_lock_expired(lock):
            raise PreventUpdate
        return build_refresh_signal()

    @app.callback(
        Output(mount.ids.refresh_lock_store_id, 'data'),
        Input(mount.ids.refresh_signal_store_id, 'data'),
        State(mount.ids.refresh_lock_store_id, 'data'),
        prevent_initial_call=True,
    )
    def acquire_refresh_lock(signal_data: object, lock_data: object) -> dict[str, object]:
        if not isinstance(signal_data, Mapping) or not signal_data:
            raise PreventUpdate
        lock = lock_data if isinstance(lock_data, Mapping) else {}
        if bool(lock.get('is_running', False)) and not is_refresh_lock_expired(lock):
            raise PreventUpdate
        return build_acquired_refresh_lock(signal_data)

    collector_dependencies = [
        *component_outputs,
        Output(mount.ids.latest_control_store_id, 'data'),
        Output(mount.ids.timeseries_control_store_id, 'data'),
        Output(mount.ids.refresh_lock_store_id, 'data', allow_duplicate=True),
        Input(mount.ids.refresh_lock_store_id, 'data'),
        State(mount.ids.refresh_signal_store_id, 'data'),
        *component_states,
        State(mount.ids.latest_control_store_id, 'data'),
        State(mount.ids.timeseries_control_store_id, 'data'),
    ]

    @app.callback(*collector_dependencies, prevent_initial_call=True)
    def collect_runtime_deliveries(lock_data: object, signal_data: object, *state_values: object):
        if not isinstance(lock_data, Mapping) or not bool(lock_data.get('is_running', False)):
            raise PreventUpdate
        if not isinstance(signal_data, Mapping):
            raise PreventUpdate
        active_token = lock_data.get('active_token')
        signal_token = signal_data.get('token')
        if not isinstance(active_token, str) or not active_token or active_token != signal_token:
            raise PreventUpdate

        component_count = len(mount.registry.components)
        expected_states = component_count * 2 + 2
        if len(state_values) != expected_states:
            raise PreventUpdate
        component_values = state_values[: component_count * 2]
        latest_current = tuple(component_values[0::2])
        timeseries_current = tuple(component_values[1::2])
        latest_control = _as_mapping(state_values[-2])
        timeseries_control = _as_mapping(state_values[-1])

        latest_plan = _collect_channel(
            channel=DeliveryChannel.LATEST,
            worker_cache=worker_cache,
            mount=mount,
            current_control=latest_control,
            current_payloads=latest_current,
        )
        timeseries_plan = _collect_channel(
            channel=DeliveryChannel.TIMESERIES,
            worker_cache=worker_cache,
            mount=mount,
            current_control=timeseries_control,
            current_payloads=timeseries_current,
        )

        component_updates: list[object] = []
        for latest_value, timeseries_value in zip(
            latest_plan.component_payloads,
            timeseries_plan.component_payloads,
            strict=True,
        ):
            component_updates.extend(
                (
                    no_update if latest_value is None else latest_value,
                    no_update if timeseries_value is None else timeseries_value,
                )
            )
        return (
            *component_updates,
            no_update if latest_plan.control is None else latest_plan.control,
            no_update if timeseries_plan.control is None else timeseries_plan.control,
            build_released_refresh_lock(),
        )


def _collect_channel(
    *,
    channel: DeliveryChannel,
    worker_cache: WorkerDeliveryCache,
    mount: RuntimeDeliveryCollectorMount,
    current_control: Mapping[str, object] | None,
    current_payloads: tuple[object, ...],
) -> RuntimeChannelUpdatePlan:
    try:
        snapshot = worker_cache.read(channel)
        return plan_channel_updates(
            channel=channel,
            snapshot=snapshot,
            registry=mount.registry,
            current_control=current_control,
            current_payloads=current_payloads,
        )
    except Exception:
        return RuntimeChannelUpdatePlan.unchanged(len(mount.registry.components))


def _as_mapping(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None
