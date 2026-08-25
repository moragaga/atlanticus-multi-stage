from datetime import UTC, datetime

from ada.runtime.component_stores import RuntimeComponentStoreRegistry, RuntimeComponentStoreSpec
from ada.runtime.delivery_cache import DeliveryChannel, DeliverySnapshot, WorkerDeliveryCache
from ada.runtime.delivery_collector import (
    build_runtime_delivery_collector_mount,
    plan_channel_updates,
    register_runtime_delivery_collector_callbacks,
)


class Repository:
    def __init__(self) -> None:
        self.reads = {DeliveryChannel.LATEST: 0, DeliveryChannel.TIMESERIES: 0}
        self.snapshots = {
            DeliveryChannel.LATEST: DeliverySnapshot(
                revision='latest-a',
                published_at_utc=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
                payload={
                    'destinations': {
                        'global_indicators': {
                            'produccion_total': {
                                'status': 'ok',
                                'value_kind': 'value',
                                'value': '66,00',
                            }
                        }
                    }
                },
            ),
            DeliveryChannel.TIMESERIES: DeliverySnapshot(
                revision='timeseries-a',
                published_at_utc=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
                payload={
                    'destinations': {'molienda': ['produccion_total']},
                    'windows': [
                        {
                            'destination': 'molienda',
                            'hours': 1,
                            'start_utc': '2026-08-25T11:00:00Z',
                            'end_utc': '2026-08-25T12:00:00Z',
                            'keys': ['produccion_total'],
                            'values': [[60.1, 62.2]],
                        }
                    ],
                },
            ),
        }

    def read(self, channel: DeliveryChannel) -> DeliverySnapshot:
        self.reads[channel] += 1
        return self.snapshots[channel]


class RecordingApp:
    def __init__(self) -> None:
        self.callbacks = []

    def callback(self, *dependencies, **options):
        def decorator(function):
            self.callbacks.append((dependencies, options, function))
            return function

        return decorator


clock = [0.0]
repository = Repository()
cache = WorkerDeliveryCache(repository, ttl_seconds=1.0, clock=lambda: clock[0])
registry = RuntimeComponentStoreRegistry(
    tool_key='operaciones_integradas',
    components=(
        RuntimeComponentStoreSpec(
            component_key='global_indicators',
            wrapper_id='ada-runtime-component-global_indicators',
            latest_store_id='ada-runtime-kpi-latest-global_indicators',
            timeseries_store_id='ada-runtime-kpi-timeseries-global_indicators',
        ),
        RuntimeComponentStoreSpec(
            component_key='molienda',
            wrapper_id='ada-runtime-component-molienda',
            latest_store_id='ada-runtime-kpi-latest-molienda',
            timeseries_store_id='ada-runtime-kpi-timeseries-molienda',
        ),
    ),
)
mount = build_runtime_delivery_collector_mount(registry, interval_ms=5_000)
app = RecordingApp()
register_runtime_delivery_collector_callbacks(app, mount=mount, worker_cache=cache)
stores = {store.id: store.data for store in mount.component_mount.stores}
latest_current = tuple(stores[component.latest_store_id] for component in registry.components)
timeseries_current = tuple(
    stores[component.timeseries_store_id] for component in registry.components
)

latest_a = cache.read(DeliveryChannel.LATEST)
latest_plan_a = plan_channel_updates(
    channel=DeliveryChannel.LATEST,
    snapshot=latest_a,
    registry=registry,
    current_control=mount.latest_control_store.data,
    current_payloads=latest_current,
)
latest_current = tuple(
    current if update is None else update
    for current, update in zip(latest_current, latest_plan_a.component_payloads, strict=True)
)

same_latest = cache.read(DeliveryChannel.LATEST)
same_plan = plan_channel_updates(
    channel=DeliveryChannel.LATEST,
    snapshot=same_latest,
    registry=registry,
    current_control=latest_plan_a.control,
    current_payloads=latest_current,
)

clock[0] = 2.0
repository.snapshots[DeliveryChannel.LATEST] = DeliverySnapshot(
    revision='latest-b',
    published_at_utc=datetime(2026, 8, 25, 12, 1, tzinfo=UTC),
    payload={
        'destinations': {
            'global_indicators': {
                'produccion_total': {
                    'status': 'ok',
                    'value_kind': 'value',
                    'value': '66,00',
                }
            },
            'molienda': {
                'produccion_total': {
                    'status': 'ok',
                    'value_kind': 'value',
                    'value': '62,10',
                }
            },
        }
    },
)
latest_b = cache.read(DeliveryChannel.LATEST)
latest_plan_b = plan_channel_updates(
    channel=DeliveryChannel.LATEST,
    snapshot=latest_b,
    registry=registry,
    current_control=latest_plan_a.control,
    current_payloads=latest_current,
)

timeseries = cache.read(DeliveryChannel.TIMESERIES)
timeseries_plan = plan_channel_updates(
    channel=DeliveryChannel.TIMESERIES,
    snapshot=timeseries,
    registry=registry,
    current_control=mount.timeseries_control_store.data,
    current_payloads=timeseries_current,
)

print('R4 protected collector POC:')
print(f'callbacks registered: {len(app.callbacks)}')
print(f'component stores: {len(mount.component_mount.stores)}')
print(f'latest repository reads inside TTL: {repository.reads[DeliveryChannel.LATEST] - 1}')
print(
    'initial latest component updates: '
    f'{sum(value is not None for value in latest_plan_a.component_payloads)}'
)
print(
    'same revision component updates: '
    f'{sum(value is not None for value in same_plan.component_payloads)}'
)
print(
    'new revision granular component updates: '
    f'{sum(value is not None for value in latest_plan_b.component_payloads)}'
)
print(f'latest revision after refresh: {latest_plan_b.control["revision"]}')
print(
    'timeseries component updates: '
    f'{sum(value is not None for value in timeseries_plan.component_payloads)}'
)
print(f'timeseries repository reads: {repository.reads[DeliveryChannel.TIMESERIES]}')
