from __future__ import annotations

import threading
import time
from datetime import UTC, datetime

from ada.runtime.delivery_cache import DeliveryChannel, DeliverySnapshot, WorkerDeliveryCache


class Repository:
    def __init__(self) -> None:
        self.calls = {channel: 0 for channel in DeliveryChannel}
        self.delay_seconds = 0.15
        self._lock = threading.Lock()
        self.latest = DeliverySnapshot(
            'latest-a',
            datetime(2026, 8, 25, 4, 10, tzinfo=UTC),
            {'destinations': {'global_indicators': {'produccion_total': '66,00'}}},
        )
        self.timeseries = DeliverySnapshot(
            'timeseries-a',
            datetime(2026, 8, 25, 4, 10, tzinfo=UTC),
            {'windows': []},
        )

    def read(self, channel: DeliveryChannel) -> DeliverySnapshot:
        with self._lock:
            self.calls[channel] += 1
        time.sleep(self.delay_seconds)
        if channel is DeliveryChannel.LATEST:
            return self.latest
        return self.timeseries


def concurrent_reads(cache: WorkerDeliveryCache, count: int) -> list[DeliverySnapshot | None]:
    barrier = threading.Barrier(count + 1)
    results: list[DeliverySnapshot | None] = []
    result_lock = threading.Lock()

    def target() -> None:
        barrier.wait()
        result = cache.read(DeliveryChannel.LATEST)
        with result_lock:
            results.append(result)

    threads = [threading.Thread(target=target) for _ in range(count)]
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join()
    return results


def main() -> None:
    repository = Repository()
    worker_a = WorkerDeliveryCache(repository, ttl_seconds=1.0)
    print(f'worker A cache id: {id(worker_a)}')

    cold_results = concurrent_reads(worker_a, 20)
    print('cold concurrent consumers: 20')
    print(f'latest repository reads: {repository.calls[DeliveryChannel.LATEST]}')
    print(f'consumers with immediate snapshot: {sum(item is not None for item in cold_results)}')

    hot_results = concurrent_reads(worker_a, 20)
    print('hot concurrent consumers inside TTL: 20')
    print(f'latest repository reads: {repository.calls[DeliveryChannel.LATEST]}')
    print(f'consumers with cached snapshot: {sum(item is not None for item in hot_results)}')

    repository.latest = DeliverySnapshot(
        'latest-b',
        datetime(2026, 8, 25, 4, 12, tzinfo=UTC),
        {'destinations': {'global_indicators': {'produccion_total': '67,20'}}},
    )
    time.sleep(1.05)
    refresh_results = concurrent_reads(worker_a, 20)
    current = worker_a.read(DeliveryChannel.LATEST)
    print('expired TTL concurrent consumers: 20')
    print(f'latest repository reads: {repository.calls[DeliveryChannel.LATEST]}')
    print(
        f'consumers served stale-or-fresh snapshot: {sum(item is not None for item in refresh_results)}'
    )
    print(f'worker A current latest revision: {current.revision if current else None}')

    timeseries = worker_a.read(DeliveryChannel.TIMESERIES)
    print(f'timeseries repository reads: {repository.calls[DeliveryChannel.TIMESERIES]}')
    print(f'worker A timeseries revision: {timeseries.revision if timeseries else None}')

    worker_b = WorkerDeliveryCache(repository, ttl_seconds=1.0)
    print(f'worker B cache id: {id(worker_b)}')
    worker_b.read(DeliveryChannel.LATEST)
    print(
        f'latest repository reads after worker B first read: {repository.calls[DeliveryChannel.LATEST]}'
    )


if __name__ == '__main__':
    main()
