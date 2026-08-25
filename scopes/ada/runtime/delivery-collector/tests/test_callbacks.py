from dataclasses import dataclass

from dash.exceptions import PreventUpdate

from ada.runtime.component_stores import RuntimeComponentStoreRegistry, RuntimeComponentStoreSpec
from ada.runtime.delivery_cache import WorkerDeliveryCache
from ada.runtime.delivery_collector import (
    build_runtime_delivery_collector_mount,
    register_runtime_delivery_collector_callbacks,
)


class _Repository:
    def read(self, channel):
        raise RuntimeError(channel)


@dataclass
class _CallbackRecord:
    dependencies: tuple[object, ...]
    options: dict[str, object]
    function: object


class _RecordingApp:
    def __init__(self) -> None:
        self.records: list[_CallbackRecord] = []

    def callback(self, *dependencies, **options):
        def decorator(function):
            self.records.append(_CallbackRecord(dependencies, options, function))
            return function

        return decorator


def _registry() -> RuntimeComponentStoreRegistry:
    return RuntimeComponentStoreRegistry(
        tool_key='operaciones_integradas',
        components=(
            RuntimeComponentStoreSpec(
                component_key='molienda',
                wrapper_id='wrapper-molienda',
                latest_store_id='latest-molienda',
                timeseries_store_id='timeseries-molienda',
            ),
        ),
    )


def test_collector_registers_exactly_three_callbacks_without_pattern_matching() -> None:
    app = _RecordingApp()
    mount = build_runtime_delivery_collector_mount(_registry(), interval_ms=5_000)

    register_runtime_delivery_collector_callbacks(
        app,
        mount=mount,
        worker_cache=WorkerDeliveryCache(_Repository()),
    )

    assert len(app.records) == 3
    assert app.records[0].options.get('prevent_initial_call') is None
    assert app.records[1].options['prevent_initial_call'] is True
    assert app.records[2].options['prevent_initial_call'] is True
    dependency_text = repr(tuple(record.dependencies for record in app.records))
    assert "'type'" not in dependency_text
    assert 'latest-molienda' in dependency_text
    assert 'timeseries-molienda' in dependency_text


def test_refresh_request_is_suppressed_while_session_lock_is_running() -> None:
    app = _RecordingApp()
    mount = build_runtime_delivery_collector_mount(_registry(), interval_ms=5_000)
    register_runtime_delivery_collector_callbacks(
        app,
        mount=mount,
        worker_cache=WorkerDeliveryCache(_Repository()),
    )
    request_refresh = app.records[0].function

    try:
        request_refresh(
            3,
            {
                'is_running': True,
                'active_token': 'active',
                'started_at_utc': '2099-08-25T12:00:00Z',
            },
        )
    except PreventUpdate:
        pass
    else:
        raise AssertionError('Running session lock must suppress new refresh signals')
