from datetime import UTC, datetime

import pytest

from ada.runtime.web import (
    Freshness,
    RuntimeDefinitionError,
    RuntimeDefinition,
    RuntimeSnapshot,
    SourceHealth,
    SourceState,
    ValueState,
    ValueStatus,
)

NOW = datetime(2026, 8, 13, 1, 30, tzinfo=UTC)


def test_shape_fills_missing_configured_entries_without_hiding_structure() -> None:
    shape = RuntimeDefinition(source_keys=('pi', 'dispatch'), value_keys=('kpi_a', 'kpi_b'))
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
        )
    )

    assert snapshot.source('pi').health is SourceHealth.HEALTHY
    assert snapshot.source('dispatch').health is SourceHealth.UNAVAILABLE
    assert snapshot.value('kpi_a').status is ValueStatus.INVALID
    assert snapshot.value('kpi_b').status is ValueStatus.NOT_MAPPED


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
