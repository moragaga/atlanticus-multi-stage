from __future__ import annotations

import threading
import time
from datetime import UTC, datetime, timedelta, timezone

import pytest

from ada.runtime.delivery_cache import (
    DeliveryCacheDefinitionError,
    DeliveryChannel,
    DeliverySnapshot,
    WorkerDeliveryCache,
)

PUBLISHED_1 = datetime(2026, 8, 25, 4, 10, tzinfo=UTC)
PUBLISHED_2 = datetime(2026, 8, 25, 4, 12, tzinfo=UTC)
PUBLISHED_3 = datetime(2026, 8, 25, 4, 14, tzinfo=UTC)


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class FakeRepository:
    def __init__(self) -> None:
        self.snapshots = {
            DeliveryChannel.LATEST: DeliverySnapshot(
                'latest-a', PUBLISHED_1, {'destinations': {'molienda': {'kpi': '66,00'}}}
            ),
            DeliveryChannel.TIMESERIES: DeliverySnapshot(
                'timeseries-a', PUBLISHED_1, {'windows': []}
            ),
        }
        self.calls = {channel: 0 for channel in DeliveryChannel}
        self.delay_seconds = 0.0
        self.fail_channels: set[DeliveryChannel] = set()
        self._lock = threading.Lock()

    def read(self, channel: DeliveryChannel) -> DeliverySnapshot:
        with self._lock:
            self.calls[channel] += 1
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        if channel in self.fail_channels:
            raise RuntimeError('repository unavailable')
        return self.snapshots[channel]


class BlockingRepository(FakeRepository):
    def __init__(self) -> None:
        super().__init__()
        self.started = threading.Event()
        self.release = threading.Event()

    def read(self, channel: DeliveryChannel) -> DeliverySnapshot:
        with self._lock:
            self.calls[channel] += 1
        self.started.set()
        if not self.release.wait(timeout=2.0):
            raise RuntimeError('test repository release timed out')
        return self.snapshots[channel]


def test_cold_cache_reads_delivery_once() -> None:
    repository = FakeRepository()
    cache = WorkerDeliveryCache(repository)

    snapshot = cache.read(DeliveryChannel.LATEST)

    assert snapshot is not None
    assert snapshot.revision == 'latest-a'
    assert repository.calls[DeliveryChannel.LATEST] == 1


def test_one_hundred_reads_inside_ttl_do_not_hit_repository_again() -> None:
    repository = FakeRepository()
    clock = FakeClock()
    cache = WorkerDeliveryCache(repository, ttl_seconds=1.0, clock=clock)
    first = cache.read(DeliveryChannel.LATEST)

    results = [cache.read(DeliveryChannel.LATEST) for _ in range(100)]

    assert first is not None
    assert all(result is first for result in results)
    assert repository.calls[DeliveryChannel.LATEST] == 1


def test_in_flight_read_never_blocks_a_second_consumer() -> None:
    repository = BlockingRepository()
    cache = WorkerDeliveryCache(repository)
    winner_result: list[DeliverySnapshot | None] = []

    winner = threading.Thread(
        target=lambda: winner_result.append(cache.read(DeliveryChannel.LATEST))
    )
    winner.start()
    assert repository.started.wait(timeout=1.0)

    started_at = time.monotonic()
    concurrent = cache.read(DeliveryChannel.LATEST)
    elapsed = time.monotonic() - started_at

    assert concurrent is None
    assert elapsed < 0.2
    assert repository.calls[DeliveryChannel.LATEST] == 1

    repository.release.set()
    winner.join(timeout=1.0)
    assert not winner.is_alive()
    assert winner_result[0] is not None


def test_twenty_cold_threads_share_one_non_blocking_repository_read() -> None:
    repository = FakeRepository()
    repository.delay_seconds = 0.08
    cache = WorkerDeliveryCache(repository)
    barrier = threading.Barrier(21)
    results: list[DeliverySnapshot | None] = []

    def target() -> None:
        barrier.wait()
        results.append(cache.read(DeliveryChannel.LATEST))

    threads = [threading.Thread(target=target) for _ in range(20)]
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join()

    assert len(results) == 20
    assert repository.calls[DeliveryChannel.LATEST] == 1
    assert any(result is not None and result.revision == 'latest-a' for result in results)
    assert all(result is None or result.revision == 'latest-a' for result in results)


def test_expired_cache_uses_last_known_good_while_one_thread_refreshes() -> None:
    repository = FakeRepository()
    clock = FakeClock()
    cache = WorkerDeliveryCache(repository, ttl_seconds=1.0, clock=clock)
    first = cache.read(DeliveryChannel.LATEST)
    assert first is not None
    repository.snapshots[DeliveryChannel.LATEST] = DeliverySnapshot(
        'latest-b', PUBLISHED_2, {'destinations': {'molienda': {'kpi': '67,20'}}}
    )
    repository.delay_seconds = 0.08
    clock.advance(1.1)
    barrier = threading.Barrier(21)
    results: list[DeliverySnapshot | None] = []

    def target() -> None:
        barrier.wait()
        results.append(cache.read(DeliveryChannel.LATEST))

    threads = [threading.Thread(target=target) for _ in range(20)]
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join()

    assert repository.calls[DeliveryChannel.LATEST] == 2
    assert all(result is not None for result in results)
    assert {result.revision for result in results if result is not None} <= {'latest-a', 'latest-b'}
    assert cache.read(DeliveryChannel.LATEST).revision == 'latest-b'


def test_latest_and_timeseries_have_independent_single_flight_entries() -> None:
    repository = FakeRepository()
    cache = WorkerDeliveryCache(repository)

    latest = cache.read(DeliveryChannel.LATEST)
    timeseries = cache.read(DeliveryChannel.TIMESERIES)
    cache.read(DeliveryChannel.LATEST)
    cache.read(DeliveryChannel.TIMESERIES)

    assert latest is not None and latest.revision == 'latest-a'
    assert timeseries is not None and timeseries.revision == 'timeseries-a'
    assert repository.calls == {
        DeliveryChannel.LATEST: 1,
        DeliveryChannel.TIMESERIES: 1,
    }


def test_repository_failure_serves_last_known_good_and_throttles_retry() -> None:
    repository = FakeRepository()
    clock = FakeClock()
    cache = WorkerDeliveryCache(repository, ttl_seconds=1.0, clock=clock)
    first = cache.read(DeliveryChannel.LATEST)
    assert first is not None
    repository.fail_channels.add(DeliveryChannel.LATEST)
    clock.advance(1.1)

    stale = cache.read(DeliveryChannel.LATEST)
    again = cache.read(DeliveryChannel.LATEST)

    assert stale is first
    assert again is first
    assert repository.calls[DeliveryChannel.LATEST] == 2


def test_newer_revision_replaces_cached_snapshot() -> None:
    repository = FakeRepository()
    clock = FakeClock()
    cache = WorkerDeliveryCache(repository, ttl_seconds=1.0, clock=clock)
    cache.read(DeliveryChannel.LATEST)
    repository.snapshots[DeliveryChannel.LATEST] = DeliverySnapshot(
        'latest-b', PUBLISHED_2, {'destinations': {'molienda': {'kpi': '67,20'}}}
    )
    clock.advance(1.1)

    snapshot = cache.read(DeliveryChannel.LATEST)

    assert snapshot is not None
    assert snapshot.revision == 'latest-b'


def test_older_snapshot_never_replaces_last_known_good() -> None:
    repository = FakeRepository()
    clock = FakeClock()
    repository.snapshots[DeliveryChannel.LATEST] = DeliverySnapshot(
        'latest-b', PUBLISHED_2, {'destinations': {'molienda': {'kpi': '67,20'}}}
    )
    cache = WorkerDeliveryCache(repository, ttl_seconds=1.0, clock=clock)
    newest = cache.read(DeliveryChannel.LATEST)
    assert newest is not None
    repository.snapshots[DeliveryChannel.LATEST] = DeliverySnapshot(
        'latest-a', PUBLISHED_1, {'destinations': {'molienda': {'kpi': '66,00'}}}
    )
    clock.advance(1.1)

    result = cache.read(DeliveryChannel.LATEST)

    assert result is newest
    assert result.revision == 'latest-b'


def test_same_revision_with_different_payload_keeps_last_known_good() -> None:
    repository = FakeRepository()
    clock = FakeClock()
    cache = WorkerDeliveryCache(repository, ttl_seconds=1.0, clock=clock)
    first = cache.read(DeliveryChannel.LATEST)
    assert first is not None
    repository.snapshots[DeliveryChannel.LATEST] = DeliverySnapshot(
        'latest-a', PUBLISHED_2, {'destinations': {'molienda': {'kpi': '99,99'}}}
    )
    clock.advance(1.1)

    result = cache.read(DeliveryChannel.LATEST)

    assert result is first
    assert result.payload['destinations'] == {'molienda': {'kpi': '66,00'}}


def test_different_revision_at_same_publication_time_keeps_last_known_good() -> None:
    repository = FakeRepository()
    clock = FakeClock()
    cache = WorkerDeliveryCache(repository, ttl_seconds=1.0, clock=clock)
    first = cache.read(DeliveryChannel.LATEST)
    assert first is not None
    repository.snapshots[DeliveryChannel.LATEST] = DeliverySnapshot(
        'latest-b', PUBLISHED_1, {'destinations': {'molienda': {'kpi': '67,20'}}}
    )
    clock.advance(1.1)

    result = cache.read(DeliveryChannel.LATEST)

    assert result is first


def test_two_cache_instances_model_two_independent_workers() -> None:
    repository = FakeRepository()
    worker_a = WorkerDeliveryCache(repository)
    worker_b = WorkerDeliveryCache(repository)

    snapshot_a = worker_a.read(DeliveryChannel.LATEST)
    snapshot_b = worker_b.read(DeliveryChannel.LATEST)

    assert worker_a is not worker_b
    assert snapshot_a is not None and snapshot_b is not None
    assert snapshot_a.revision == snapshot_b.revision == 'latest-a'
    assert repository.calls[DeliveryChannel.LATEST] == 2


def test_clear_can_drop_one_channel_without_touching_the_other() -> None:
    repository = FakeRepository()
    cache = WorkerDeliveryCache(repository)
    cache.read(DeliveryChannel.LATEST)
    cache.read(DeliveryChannel.TIMESERIES)

    cache.clear(DeliveryChannel.LATEST)
    cache.read(DeliveryChannel.LATEST)
    cache.read(DeliveryChannel.TIMESERIES)

    assert repository.calls == {
        DeliveryChannel.LATEST: 2,
        DeliveryChannel.TIMESERIES: 1,
    }


def test_snapshot_copies_payload_and_requires_utc_metadata() -> None:
    payload = {'destinations': {'molienda': {'kpi': '66,00'}}}
    snapshot = DeliverySnapshot(' latest-a ', PUBLISHED_1, payload)
    payload['destinations']['molienda']['kpi'] = '99,99'

    assert snapshot.revision == 'latest-a'
    assert snapshot.payload['destinations'] == {'molienda': {'kpi': '66,00'}}
    with pytest.raises(DeliveryCacheDefinitionError, match='timezone-aware'):
        DeliverySnapshot('latest-a', datetime(2026, 8, 25, 4, 10), {})
    with pytest.raises(DeliveryCacheDefinitionError, match='must use UTC'):
        DeliverySnapshot(
            'latest-a', datetime(2026, 8, 25, 5, 10, tzinfo=timezone(timedelta(hours=1))), {}
        )


def test_cache_rejects_invalid_configuration_and_channel() -> None:
    repository = FakeRepository()
    with pytest.raises(DeliveryCacheDefinitionError, match='ttl_seconds'):
        WorkerDeliveryCache(repository, ttl_seconds=0)
    cache = WorkerDeliveryCache(repository)
    with pytest.raises(DeliveryCacheDefinitionError, match='Invalid delivery channel'):
        cache.read('latest')
