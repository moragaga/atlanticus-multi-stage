from __future__ import annotations

from dataclasses import dataclass

from dash import dcc, html

from ada.runtime.component_stores import (
    RuntimeComponentStoreMount,
    RuntimeComponentStoreRegistry,
    build_runtime_component_store_mount,
)

from .errors import RuntimeDeliveryCollectorError
from .refresh import build_released_refresh_lock


@dataclass(frozen=True, slots=True)
class RuntimeDeliveryCollectorIds:
    interval_id: str
    refresh_signal_store_id: str
    refresh_lock_store_id: str
    latest_control_store_id: str
    timeseries_control_store_id: str


@dataclass(frozen=True, slots=True)
class RuntimeDeliveryCollectorMount:
    registry: RuntimeComponentStoreRegistry
    component_mount: RuntimeComponentStoreMount
    ids: RuntimeDeliveryCollectorIds
    interval: dcc.Interval
    refresh_signal_store: dcc.Store
    refresh_lock_store: dcc.Store
    latest_control_store: dcc.Store
    timeseries_control_store: dcc.Store

    def runtime_host(self) -> html.Div:
        return html.Div(
            [
                self.interval,
                self.refresh_signal_store,
                self.refresh_lock_store,
                self.latest_control_store,
                self.timeseries_control_store,
                *self.component_mount.stores,
            ],
            style={'display': 'none'},
        )


def build_runtime_delivery_collector_mount(
    registry: RuntimeComponentStoreRegistry,
    *,
    interval_ms: int,
) -> RuntimeDeliveryCollectorMount:
    if isinstance(interval_ms, bool) or not isinstance(interval_ms, int) or interval_ms <= 0:
        raise RuntimeDeliveryCollectorError(
            'Runtime collector interval_ms must be a positive integer'
        )
    ids = _build_ids(registry.tool_key)
    component_mount = build_runtime_component_store_mount(registry)
    return RuntimeDeliveryCollectorMount(
        registry=registry,
        component_mount=component_mount,
        ids=ids,
        interval=dcc.Interval(id=ids.interval_id, interval=interval_ms, n_intervals=0),
        refresh_signal_store=dcc.Store(
            id=ids.refresh_signal_store_id,
            data=None,
            storage_type='memory',
        ),
        refresh_lock_store=dcc.Store(
            id=ids.refresh_lock_store_id,
            data=build_released_refresh_lock(),
            storage_type='memory',
        ),
        latest_control_store=dcc.Store(
            id=ids.latest_control_store_id,
            data={'revision': None, 'published_at_utc': None},
            storage_type='memory',
        ),
        timeseries_control_store=dcc.Store(
            id=ids.timeseries_control_store_id,
            data={'revision': None, 'published_at_utc': None},
            storage_type='memory',
        ),
    )


def _build_ids(tool_key: str) -> RuntimeDeliveryCollectorIds:
    key = tool_key.strip() if isinstance(tool_key, str) else ''
    if not key:
        raise RuntimeDeliveryCollectorError('Runtime collector tool key cannot be empty')
    prefix = f'ada-runtime-kpi-{key}'
    return RuntimeDeliveryCollectorIds(
        interval_id=f'{prefix}-refresh-interval',
        refresh_signal_store_id=f'{prefix}-refresh-signal',
        refresh_lock_store_id=f'{prefix}-refresh-lock',
        latest_control_store_id=f'{prefix}-latest-control',
        timeseries_control_store_id=f'{prefix}-timeseries-control',
    )
