from datetime import UTC, datetime

from ada.runtime.web import (
    GuardState,
    RuntimeSnapshot,
    SourceState,
    ValueState,
    resolve_guard,
)

NOW = datetime(2026, 8, 13, 1, 30, tzinfo=UTC)


def test_guard_precedence_is_construction_component_source_stale_ready() -> None:
    snapshot = RuntimeSnapshot(
        revision='r1',
        loaded_at_utc=NOW,
        sources={'pi': SourceState.invalid('pi')},
    )

    construction = resolve_guard(snapshot, required_sources=('pi',), construction=True)
    component_error = resolve_guard(snapshot, required_sources=('pi',), component_error=True)

    assert construction.state is GuardState.CONSTRUCTION
    assert component_error.state is GuardState.COMPONENT_ERROR
    assert resolve_guard(snapshot, required_sources=('pi',)).state is GuardState.SOURCE_ERROR


def test_bad_values_do_not_turn_healthy_source_into_source_error() -> None:
    snapshot = RuntimeSnapshot(
        revision='r1',
        loaded_at_utc=NOW,
        sources={'pi': SourceState.healthy('pi', updated_at_utc=NOW)},
        values={
            'kpi_a': ValueState.invalid('kpi_a'),
            'kpi_b': ValueState.invalid('kpi_b'),
            'kpi_c': ValueState.invalid('kpi_c'),
        },
    )

    result = resolve_guard(snapshot, required_sources=('pi',))

    assert result.state is GuardState.READY


def test_stale_source_covers_component_from_first_render() -> None:
    snapshot = RuntimeSnapshot(
        revision='r1',
        loaded_at_utc=NOW,
        sources={'pi': SourceState.healthy('pi', updated_at_utc=NOW, stale=True)},
    )

    result = resolve_guard(snapshot, required_sources=('pi',))

    assert result.state is GuardState.STALE
    assert result.affected_sources == ('pi',)
