from dash import Dash, html

from ada.runtime.component_stores import RuntimeComponentStoreRegistry, RuntimeComponentStoreSpec
from ada.runtime.delivery_cache import WorkerDeliveryCache
from ada.runtime.delivery_collector import (
    build_runtime_delivery_collector_mount,
    register_runtime_delivery_collector_callbacks,
)


class _Repository:
    def read(self, channel):
        raise RuntimeError(channel)


def test_real_dash_registers_protected_collector_graph() -> None:
    registry = RuntimeComponentStoreRegistry(
        tool_key='operaciones_integradas',
        components=(
            RuntimeComponentStoreSpec(
                component_key='global_indicators',
                wrapper_id='wrapper-global',
                latest_store_id='latest-global',
                timeseries_store_id='timeseries-global',
            ),
            RuntimeComponentStoreSpec(
                component_key='molienda',
                wrapper_id='wrapper-molienda',
                latest_store_id='latest-molienda',
                timeseries_store_id='timeseries-molienda',
            ),
        ),
    )
    mount = build_runtime_delivery_collector_mount(registry, interval_ms=5_000)
    app = Dash(__name__)
    app.layout = html.Div([mount.runtime_host()])

    register_runtime_delivery_collector_callbacks(
        app,
        mount=mount,
        worker_cache=WorkerDeliveryCache(_Repository()),
    )

    assert len(app.callback_map) == 3
    callback_keys = tuple(app.callback_map)
    assert any(mount.ids.refresh_signal_store_id in key for key in callback_keys)
    assert any(mount.ids.refresh_lock_store_id in key for key in callback_keys)
    assert any('latest-global' in key and 'timeseries-molienda' in key for key in callback_keys)
