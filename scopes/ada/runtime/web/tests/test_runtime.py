from __future__ import annotations

from datetime import UTC, datetime, timedelta
from threading import Event, Thread

from ada.runtime.web import (
    AdaRuntime,
    RefreshState,
    RuntimeDefinition,
    RuntimeSnapshot,
    SourceHealth,
    SourceState,
    ValueStatus,
)

NOW = datetime(2026, 8, 13, 1, 30, tzinfo=UTC)


class ManualClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def test_runtime_warmup_swaps_complete_snapshot_atomically() -> None:
    shape = RuntimeDefinition(source_keys=('pi',), value_keys=('kpi_a',))
    runtime = AdaRuntime(
        shape=shape,
        loader=lambda: RuntimeSnapshot(
            revision='r1',
            loaded_at_utc=NOW,
            sources={'pi': SourceState.healthy('pi', updated_at_utc=NOW)},
        ),
        refresh_interval_seconds=10,
    )

    before = runtime.current()
    result = runtime.warmup()
    after = runtime.current()

    assert before.snapshot.source('pi').health is SourceHealth.UNAVAILABLE
    assert result.state is RefreshState.UPDATED
    assert after.version == 1
    assert after.snapshot.revision == 'r1'
    assert after.snapshot.value('kpi_a').status is ValueStatus.NOT_MAPPED


def test_runtime_does_not_publish_new_version_when_revision_did_not_change() -> None:
    clock = ManualClock()
    snapshot = RuntimeSnapshot(
        revision='r1',
        loaded_at_utc=NOW,
        sources={'pi': SourceState.healthy('pi', updated_at_utc=NOW)},
    )
    runtime = AdaRuntime(
        shape=RuntimeDefinition(source_keys=('pi',)),
        loader=lambda: snapshot,
        refresh_interval_seconds=10,
        monotonic=clock,
    )

    assert runtime.warmup().state is RefreshState.UPDATED
    clock.advance(10)
    result = runtime.refresh_if_due()

    assert result.state is RefreshState.UNCHANGED
    assert runtime.current().version == 1


def test_runtime_refresh_failure_publishes_safe_error_snapshot() -> None:
    def broken_loader() -> RuntimeSnapshot:
        raise TimeoutError('Cosmos is unavailable')

    runtime = AdaRuntime(
        shape=RuntimeDefinition(source_keys=('pi',), value_keys=('kpi_a',)),
        loader=broken_loader,
        refresh_interval_seconds=10,
        utcnow=lambda: NOW,
    )

    result = runtime.warmup()
    current = runtime.current()

    assert result.state is RefreshState.UPDATED
    assert result.error_type == 'TimeoutError'
    assert current.snapshot.source('pi').health is SourceHealth.ERROR
    assert current.snapshot.value('kpi_a').status is ValueStatus.ERROR
    assert current.snapshot.revision == 'runtime-error:TimeoutError'


def test_runtime_skips_queued_refresh_while_slow_loader_is_running() -> None:
    started = Event()
    release = Event()

    def slow_loader() -> RuntimeSnapshot:
        started.set()
        release.wait(timeout=2)
        return RuntimeSnapshot(
            revision='r1',
            loaded_at_utc=NOW,
            sources={'pi': SourceState.healthy('pi', updated_at_utc=NOW)},
        )

    runtime = AdaRuntime(
        shape=RuntimeDefinition(source_keys=('pi',)),
        loader=slow_loader,
        refresh_interval_seconds=10,
    )
    results = []
    thread = Thread(target=lambda: results.append(runtime.warmup()))
    thread.start()
    assert started.wait(timeout=1)

    queued = runtime.warmup()
    current_during_refresh = runtime.current()
    release.set()
    thread.join(timeout=2)

    assert queued.state is RefreshState.BUSY
    assert current_during_refresh.snapshot.revision == 'bootstrap'
    assert results[0].state is RefreshState.UPDATED


def test_refresh_if_due_does_not_call_loader_before_deadline() -> None:
    clock = ManualClock()
    calls = 0

    def loader() -> RuntimeSnapshot:
        nonlocal calls
        calls += 1
        return RuntimeSnapshot(
            revision=f'r{calls}',
            loaded_at_utc=NOW + timedelta(seconds=calls),
        )

    runtime = AdaRuntime(
        shape=RuntimeDefinition(),
        loader=loader,
        refresh_interval_seconds=10,
        monotonic=clock,
    )

    runtime.warmup()
    clock.advance(9)
    result = runtime.refresh_if_due()

    assert result.state is RefreshState.NOT_DUE
    assert calls == 1


def test_source_state_change_publishes_version_even_when_data_revision_is_same() -> None:
    clock = ManualClock()
    snapshots = iter(
        (
            RuntimeSnapshot(
                revision='r1',
                loaded_at_utc=NOW,
                sources={'pi': SourceState.healthy('pi', updated_at_utc=NOW)},
            ),
            RuntimeSnapshot(
                revision='r1',
                loaded_at_utc=NOW + timedelta(seconds=10),
                sources={
                    'pi': SourceState.healthy(
                        'pi',
                        updated_at_utc=NOW,
                        stale=True,
                    )
                },
            ),
        )
    )
    runtime = AdaRuntime(
        shape=RuntimeDefinition(source_keys=('pi',)),
        loader=lambda: next(snapshots),
        refresh_interval_seconds=10,
        monotonic=clock,
    )

    runtime.warmup()
    clock.advance(10)
    result = runtime.refresh_if_due()

    assert result.state is RefreshState.UPDATED
    assert runtime.current().version == 2
    assert runtime.current().snapshot.source('pi').freshness.value == 'stale'
