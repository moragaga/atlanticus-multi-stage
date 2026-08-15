from __future__ import annotations

import threading
import time
from collections.abc import Mapping
from datetime import UTC, datetime

import pytest

from ada.runtime.web import (
    RuntimeDefinitionError,
    SharedSnapshot,
    SharedSnapshotConsistencyError,
    SharedSnapshotReader,
    SnapshotChannel,
    snapshot_revision_datetime_utc,
)

V1 = '20260815190000000001'
V2 = '20260815190000000002'
V3 = '20260815190000000003'


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class FakeRepository:
    def __init__(self, revision: str = V1, payload: Mapping[str, object] | None = None) -> None:
        self.revision = revision
        self.payload = dict(payload or {'flotacion': {'ley': 1.2}})
        self.revision_calls = 0
        self.snapshot_calls = 0
        self.delay_seconds = 0.0

    def read_revision(self, tool_key: str, channel: SnapshotChannel) -> str:
        self.revision_calls += 1
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        return self.revision

    def read_snapshot(self, tool_key: str, channel: SnapshotChannel) -> SharedSnapshot:
        self.snapshot_calls += 1
        return SharedSnapshot(self.revision, self.payload)


class RacingRepository(FakeRepository):
    def __init__(self) -> None:
        super().__init__(V1)
        self._first_revision_read = True

    def read_revision(self, tool_key: str, channel: SnapshotChannel) -> str:
        self.revision_calls += 1
        if self._first_revision_read:
            self._first_revision_read = False
            return V1
        return V2

    def read_snapshot(self, tool_key: str, channel: SnapshotChannel) -> SharedSnapshot:
        self.snapshot_calls += 1
        return SharedSnapshot(V2, {'flotacion': {'ley': 2.0}})


class MutableSnapshotRepository(FakeRepository):
    def __init__(self, revision: str = V1) -> None:
        super().__init__(revision)
        self.snapshot_revision: str | None = None

    def read_snapshot(self, tool_key: str, channel: SnapshotChannel) -> SharedSnapshot:
        self.snapshot_calls += 1
        return SharedSnapshot(self.snapshot_revision or self.revision, self.payload)


def test_shared_snapshot_revision_is_fixed_width_utc_timestamp() -> None:
    parsed = snapshot_revision_datetime_utc('20260815193545123456')

    assert parsed == datetime(2026, 8, 15, 19, 35, 45, 123456, tzinfo=UTC)


@pytest.mark.parametrize(
    'revision',
    [
        '',
        '20260815193545',
        '2026081519354512345X',
        '20261315193545123456',
        '20260230193545123456',
    ],
)
def test_shared_snapshot_revision_rejects_invalid_values(revision: str) -> None:
    with pytest.raises(RuntimeDefinitionError, match='Shared snapshot revision'):
        SharedSnapshot(revision, {})


def test_shared_snapshot_freezes_top_level_payload() -> None:
    payload = {'flotacion': {'ley': 1.2}}
    snapshot = SharedSnapshot(V1, payload)
    payload['molienda'] = {'potencia': 10}

    assert 'molienda' not in snapshot.payload
    with pytest.raises(TypeError):
        snapshot.payload['puerto'] = {}


def test_cold_reader_fetches_revision_and_snapshot_once() -> None:
    repository = FakeRepository()
    reader = SharedSnapshotReader(repository)

    snapshot = reader.read('integrated_operations', SnapshotChannel.DATA)

    assert snapshot is not None
    assert snapshot.revision == V1
    assert repository.revision_calls == 1
    assert repository.snapshot_calls == 1


def test_hot_reader_returns_no_update_for_same_client_revision_without_repository_read() -> None:
    repository = FakeRepository()
    clock = FakeClock()
    reader = SharedSnapshotReader(repository, ttl_seconds=1.0, clock=clock)
    reader.read('integrated_operations', SnapshotChannel.DATA)

    result = reader.read(
        'integrated_operations',
        SnapshotChannel.DATA,
        client_revision=V1,
    )

    assert result is None
    assert repository.revision_calls == 1
    assert repository.snapshot_calls == 1


def test_hot_reader_serves_cached_snapshot_to_older_client_without_repository_read() -> None:
    repository = FakeRepository(V2)
    clock = FakeClock()
    reader = SharedSnapshotReader(repository, ttl_seconds=1.0, clock=clock)
    reader.read('integrated_operations', SnapshotChannel.DATA)

    result = reader.read(
        'integrated_operations',
        SnapshotChannel.DATA,
        client_revision=V1,
    )

    assert result is not None
    assert result.revision == V2
    assert repository.revision_calls == 1
    assert repository.snapshot_calls == 1


def test_expired_cache_reads_only_revision_when_shared_snapshot_did_not_change() -> None:
    repository = FakeRepository()
    clock = FakeClock()
    reader = SharedSnapshotReader(repository, ttl_seconds=1.0, clock=clock)
    reader.read('integrated_operations', SnapshotChannel.DATA)
    clock.advance(1.1)

    result = reader.read(
        'integrated_operations',
        SnapshotChannel.DATA,
        client_revision=V1,
    )

    assert result is None
    assert repository.revision_calls == 2
    assert repository.snapshot_calls == 1


def test_changed_shared_revision_fetches_snapshot_once() -> None:
    repository = FakeRepository(V1)
    clock = FakeClock()
    reader = SharedSnapshotReader(repository, ttl_seconds=1.0, clock=clock)
    reader.read('integrated_operations', SnapshotChannel.DATA)
    repository.revision = V2
    repository.payload = {'flotacion': {'ley': 2.0}}
    clock.advance(1.1)

    result = reader.read(
        'integrated_operations',
        SnapshotChannel.DATA,
        client_revision=V1,
    )

    assert result is not None
    assert result.revision == V2
    assert result.payload['flotacion'] == {'ley': 2.0}
    assert repository.revision_calls == 2
    assert repository.snapshot_calls == 2


def test_cold_worker_does_not_download_snapshot_when_client_already_has_shared_revision() -> None:
    repository = FakeRepository(V2)
    clock = FakeClock()
    reader = SharedSnapshotReader(repository, ttl_seconds=1.0, clock=clock)

    result = reader.read(
        'integrated_operations',
        SnapshotChannel.DATA,
        client_revision=V2,
    )

    assert result is None
    assert repository.revision_calls == 1
    assert repository.snapshot_calls == 0

    again = reader.read(
        'integrated_operations',
        SnapshotChannel.DATA,
        client_revision=V2,
    )
    assert again is None
    assert repository.revision_calls == 1
    assert repository.snapshot_calls == 0


def test_revision_only_cache_downloads_payload_for_new_client_without_rechecking_revision() -> None:
    repository = FakeRepository(V2)
    clock = FakeClock()
    reader = SharedSnapshotReader(repository, ttl_seconds=1.0, clock=clock)
    reader.read('integrated_operations', SnapshotChannel.DATA, client_revision=V2)

    result = reader.read('integrated_operations', SnapshotChannel.DATA)

    assert result is not None
    assert result.revision == V2
    assert repository.revision_calls == 1
    assert repository.snapshot_calls == 1


def test_client_ahead_of_local_cache_forces_revalidation_and_never_receives_older_snapshot() -> (
    None
):
    repository = FakeRepository(V1)
    clock = FakeClock()
    reader = SharedSnapshotReader(repository, ttl_seconds=10.0, clock=clock)
    reader.read('integrated_operations', SnapshotChannel.DATA)

    repository.revision = V2
    repository.payload = {'flotacion': {'ley': 2.0}}
    result = reader.read(
        'integrated_operations',
        SnapshotChannel.DATA,
        client_revision=V2,
    )

    assert result is None
    assert repository.revision_calls == 2
    assert repository.snapshot_calls == 1

    cached = reader.read('integrated_operations', SnapshotChannel.DATA)
    assert cached is not None
    assert cached.revision == V2
    assert repository.revision_calls == 2
    assert repository.snapshot_calls == 2


def test_client_ahead_of_shared_repository_is_not_downgraded() -> None:
    repository = FakeRepository(V1)
    reader = SharedSnapshotReader(repository)

    result = reader.read(
        'integrated_operations',
        SnapshotChannel.DATA,
        client_revision=V2,
    )

    assert result is None
    assert repository.revision_calls == 1
    assert repository.snapshot_calls == 0


def test_two_threads_share_one_in_flight_repository_read_per_worker() -> None:
    repository = FakeRepository()
    repository.delay_seconds = 0.05
    reader = SharedSnapshotReader(repository)
    barrier = threading.Barrier(3)
    results: list[SharedSnapshot | None] = []

    def target() -> None:
        barrier.wait()
        results.append(reader.read('integrated_operations', SnapshotChannel.DATA))

    first = threading.Thread(target=target)
    second = threading.Thread(target=target)
    first.start()
    second.start()
    barrier.wait()
    first.join()
    second.join()

    assert len(results) == 2
    assert all(item is not None and item.revision == V1 for item in results)
    assert repository.revision_calls == 1
    assert repository.snapshot_calls == 1


def test_publication_between_revision_and_snapshot_reads_is_accepted_after_confirmation() -> None:
    repository = RacingRepository()
    reader = SharedSnapshotReader(repository)

    result = reader.read('integrated_operations', SnapshotChannel.DATA)

    assert result is not None
    assert result.revision == V2
    assert repository.revision_calls == 2
    assert repository.snapshot_calls == 1


def test_inconsistent_snapshot_never_replaces_last_valid_worker_cache() -> None:
    repository = MutableSnapshotRepository(V1)
    clock = FakeClock()
    reader = SharedSnapshotReader(repository, ttl_seconds=1.0, clock=clock)
    first = reader.read('integrated_operations', SnapshotChannel.DATA)
    assert first is not None and first.revision == V1

    repository.revision = V2
    repository.snapshot_revision = V1
    clock.advance(1.1)
    with pytest.raises(SharedSnapshotConsistencyError, match='does not match'):
        reader.read(
            'integrated_operations',
            SnapshotChannel.DATA,
            client_revision=V1,
        )

    repository.revision = V1
    repository.snapshot_revision = None
    clock.advance(1.1)
    recovered = reader.read('integrated_operations', SnapshotChannel.DATA)

    assert recovered is not None
    assert recovered.revision == V1
    assert repository.snapshot_calls == 2


def test_clear_discards_only_worker_local_cache() -> None:
    repository = FakeRepository()
    reader = SharedSnapshotReader(repository)
    reader.read('integrated_operations', SnapshotChannel.DATA)

    reader.clear()
    reader.read('integrated_operations', SnapshotChannel.DATA)

    assert repository.revision_calls == 2
    assert repository.snapshot_calls == 2


def test_reader_rejects_invalid_tool_channel_ttl_and_client_revision() -> None:
    repository = FakeRepository()

    with pytest.raises(RuntimeDefinitionError, match='ttl_seconds'):
        SharedSnapshotReader(repository, ttl_seconds=0)

    reader = SharedSnapshotReader(repository)
    with pytest.raises(RuntimeDefinitionError, match='Invalid tool key'):
        reader.read('Integrated Operations', SnapshotChannel.DATA)
    with pytest.raises(RuntimeDefinitionError, match='Invalid shared snapshot channel'):
        reader.read('integrated_operations', 'data')
    with pytest.raises(RuntimeDefinitionError, match='Shared snapshot revision'):
        reader.read(
            'integrated_operations',
            SnapshotChannel.DATA,
            client_revision='invalid',
        )
