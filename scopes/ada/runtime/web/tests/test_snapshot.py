from datetime import UTC, datetime, timedelta

import pytest

from ada.runtime.web import (
    Freshness,
    RuntimeDefinition,
    RuntimeDefinitionError,
    RuntimeSnapshot,
    RuntimeSourceDefinition,
    SourceHealth,
    SourceState,
    ValueState,
    ValueStatus,
)

NOW = datetime(2026, 8, 13, 1, 30, tzinfo=UTC)


def _source(key: str = 'pi', stale_after_seconds: int = 300) -> RuntimeSourceDefinition:
    return RuntimeSourceDefinition(key=key, stale_after_seconds=stale_after_seconds)


def test_shape_fills_missing_configured_entries_without_hiding_structure() -> None:
    shape = RuntimeDefinition(
        sources=(_source('pi'), _source('dispatch', 600)),
        value_keys=('kpi_a', 'kpi_b'),
    )
    snapshot = shape.normalize(
        RuntimeSnapshot(
            revision='r1',
            loaded_at_utc=NOW,
            sources={
                'pi': SourceState.healthy('pi', updated_at_utc=NOW),
            },
            values={
                'kpi_a': ValueState.invalid('kpi_a'),
            },
        ),
        evaluated_at_utc=NOW,
    )

    assert snapshot.source('pi').health is SourceHealth.HEALTHY
    assert snapshot.source('pi').freshness is Freshness.FRESH
    assert snapshot.source('dispatch').health is SourceHealth.UNAVAILABLE
    assert snapshot.value('kpi_a').status is ValueStatus.INVALID
    assert snapshot.value('kpi_b').status is ValueStatus.NOT_MAPPED


def test_shape_does_not_publish_sources_without_a_runtime_definition() -> None:
    shape = RuntimeDefinition(sources=(_source('pi'),))
    snapshot = shape.normalize(
        RuntimeSnapshot(
            revision='r1',
            loaded_at_utc=NOW,
            sources={
                'pi': SourceState.healthy('pi', updated_at_utc=NOW),
                'dispatch': SourceState.healthy('dispatch', updated_at_utc=NOW),
            },
        ),
        evaluated_at_utc=NOW,
    )

    assert tuple(snapshot.sources) == ('pi',)


def test_runtime_source_definition_computes_freshness_from_real_age() -> None:
    shape = RuntimeDefinition(sources=(_source(stale_after_seconds=300),))
    candidate = RuntimeSnapshot(
        revision='r1',
        loaded_at_utc=NOW,
        sources={
            'pi': SourceState.healthy(
                'pi',
                updated_at_utc=NOW - timedelta(seconds=299),
                stale=True,
            )
        },
    )

    snapshot = shape.normalize(candidate, evaluated_at_utc=NOW)

    assert snapshot.source('pi').freshness is Freshness.FRESH


def test_runtime_source_definition_marks_exact_threshold_as_stale() -> None:
    shape = RuntimeDefinition(sources=(_source(stale_after_seconds=300),))
    snapshot = shape.normalize(
        RuntimeSnapshot(
            revision='r1',
            loaded_at_utc=NOW,
            sources={
                'pi': SourceState.healthy(
                    'pi',
                    updated_at_utc=NOW - timedelta(seconds=300),
                )
            },
        ),
        evaluated_at_utc=NOW,
    )

    assert snapshot.source('pi').freshness is Freshness.STALE


def test_runtime_source_definition_treats_future_timestamp_as_fresh() -> None:
    shape = RuntimeDefinition(sources=(_source(stale_after_seconds=300),))
    snapshot = shape.normalize(
        RuntimeSnapshot(
            revision='r1',
            loaded_at_utc=NOW,
            sources={
                'pi': SourceState.healthy(
                    'pi',
                    updated_at_utc=NOW + timedelta(seconds=30),
                )
            },
        ),
        evaluated_at_utc=NOW,
    )

    assert snapshot.source('pi').freshness is Freshness.FRESH


def test_unhealthy_source_keeps_unknown_freshness() -> None:
    shape = RuntimeDefinition(sources=(_source(),))
    snapshot = shape.normalize(
        RuntimeSnapshot(
            revision='r1',
            loaded_at_utc=NOW,
            sources={'pi': SourceState.invalid('pi', updated_at_utc=NOW)},
        ),
        evaluated_at_utc=NOW + timedelta(hours=1),
    )

    assert snapshot.source('pi').health is SourceHealth.INVALID
    assert snapshot.source('pi').freshness is Freshness.UNKNOWN


@pytest.mark.parametrize('value', (0, -1, True, 1.5))
def test_runtime_source_definition_rejects_invalid_threshold(value) -> None:
    with pytest.raises(RuntimeDefinitionError):
        RuntimeSourceDefinition('pi', stale_after_seconds=value)


def test_runtime_definition_rejects_duplicate_source_keys() -> None:
    with pytest.raises(RuntimeDefinitionError, match='Duplicate source keys'):
        RuntimeDefinition(sources=(_source('pi', 300), _source('pi', 600)))


def test_missing_identifier_lookup_is_safe() -> None:
    snapshot = RuntimeSnapshot(revision='r1', loaded_at_utc=NOW)

    assert snapshot.source('pi').health is SourceHealth.UNAVAILABLE
    assert snapshot.value('unknown_kpi').status is ValueStatus.NOT_MAPPED


def test_degraded_value_cannot_expose_previous_value_as_current() -> None:
    with pytest.raises(RuntimeDefinitionError, match='cannot expose a fallback value'):
        ValueState('kpi_a', ValueStatus.INVALID, 89.4)


def test_healthy_source_requires_timestamp_and_freshness() -> None:
    with pytest.raises(RuntimeDefinitionError, match='requires updated_at_utc'):
        SourceState('pi', SourceHealth.HEALTHY, Freshness.FRESH)
