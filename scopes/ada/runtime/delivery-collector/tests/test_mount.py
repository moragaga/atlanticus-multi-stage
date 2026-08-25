from dash import dcc, html

from ada.runtime.component_stores import RuntimeComponentStoreRegistry, RuntimeComponentStoreSpec
from ada.runtime.delivery_collector import build_runtime_delivery_collector_mount


def _registry() -> RuntimeComponentStoreRegistry:
    return RuntimeComponentStoreRegistry(
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


def test_mount_materializes_session_controls_and_r3_component_stores() -> None:
    mount = build_runtime_delivery_collector_mount(_registry(), interval_ms=5_000)

    assert isinstance(mount.interval, dcc.Interval)
    assert mount.interval.n_intervals == 0
    assert mount.interval.interval == 5_000
    assert len(mount.component_mount.stores) == 4
    assert mount.latest_control_store.data == {'revision': None, 'published_at_utc': None}
    assert mount.timeseries_control_store.data == {'revision': None, 'published_at_utc': None}


def test_mount_uses_deterministic_string_control_ids() -> None:
    mount = build_runtime_delivery_collector_mount(_registry(), interval_ms=5_000)

    assert mount.ids.interval_id == 'ada-runtime-kpi-operaciones_integradas-refresh-interval'
    assert (
        mount.ids.refresh_signal_store_id == 'ada-runtime-kpi-operaciones_integradas-refresh-signal'
    )
    assert mount.ids.refresh_lock_store_id == 'ada-runtime-kpi-operaciones_integradas-refresh-lock'
    assert (
        mount.ids.latest_control_store_id == 'ada-runtime-kpi-operaciones_integradas-latest-control'
    )
    assert (
        mount.ids.timeseries_control_store_id
        == 'ada-runtime-kpi-operaciones_integradas-timeseries-control'
    )


def test_runtime_host_is_hidden_and_contains_all_runtime_state() -> None:
    mount = build_runtime_delivery_collector_mount(_registry(), interval_ms=5_000)

    host = mount.runtime_host()

    assert isinstance(host, html.Div)
    assert host.style == {'display': 'none'}
    assert len(host.children) == 5 + len(mount.component_mount.stores)
