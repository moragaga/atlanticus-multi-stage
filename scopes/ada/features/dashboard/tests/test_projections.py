from datetime import UTC, datetime, timedelta, timezone

import pytest

from ada.features.dashboard import (
    ComponentDataSnapshot,
    ComponentProjectionState,
    ComponentStateSnapshot,
    ComponentTimeSeriesSnapshot,
    TimeSeriesWindowSnapshot,
)
from ada.runtime.web import RuntimeDefinitionError


def test_component_data_snapshot_preserves_missing_and_explicit_none_semantics() -> None:
    snapshot = ComponentDataSnapshot(
        component_key='flotacion',
        payload={'ley': None, 'recuperacion': 87.2},
    )

    assert 'ley' in snapshot.payload
    assert snapshot.payload['ley'] is None
    assert 'flujo' not in snapshot.payload


def test_component_data_snapshot_freezes_top_level_payload() -> None:
    payload = {'value': 1}
    snapshot = ComponentDataSnapshot(component_key='molienda', payload=payload)
    payload['value'] = 2

    assert snapshot.payload['value'] == 1
    with pytest.raises(TypeError):
        snapshot.payload['value'] = 3


def test_time_series_window_normalizes_aware_timestamps_to_utc() -> None:
    local_tz = timezone(timedelta(hours=-4))
    window = TimeSeriesWindowSnapshot(
        hours=1,
        start_utc=datetime(2026, 8, 15, 8, 0, tzinfo=local_tz),
        end_utc=datetime(2026, 8, 15, 9, 0, tzinfo=local_tz),
        series={'flujo': [1, None, 3]},
    )

    assert window.start_utc == datetime(2026, 8, 15, 12, 0, tzinfo=UTC)
    assert window.end_utc == datetime(2026, 8, 15, 13, 0, tzinfo=UTC)
    assert window.series['flujo'] == (1, None, 3)


def test_time_series_window_requires_duration_to_match_hours() -> None:
    with pytest.raises(RuntimeDefinitionError, match='duration must match hours'):
        TimeSeriesWindowSnapshot(
            hours=5,
            start_utc=datetime(2026, 8, 15, 0, 0, tzinfo=UTC),
            end_utc=datetime(2026, 8, 15, 4, 0, tzinfo=UTC),
            series={'ley': [1]},
        )


def test_time_series_window_rejects_microseconds() -> None:
    with pytest.raises(RuntimeDefinitionError, match='cannot contain microseconds'):
        TimeSeriesWindowSnapshot(
            hours=1,
            start_utc=datetime(2026, 8, 15, 0, 0, 0, 1, tzinfo=UTC),
            end_utc=datetime(2026, 8, 15, 1, 0, 0, 1, tzinfo=UTC),
            series={'ley': [1]},
        )


def test_component_time_series_snapshot_groups_unique_horizons() -> None:
    one_hour = TimeSeriesWindowSnapshot(
        hours=1,
        start_utc=datetime(2026, 8, 15, 11, 0, tzinfo=UTC),
        end_utc=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        series={'a': [1]},
    )
    five_hours = TimeSeriesWindowSnapshot(
        hours=5,
        start_utc=datetime(2026, 8, 15, 7, 0, tzinfo=UTC),
        end_utc=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        series={'b': [2]},
    )

    snapshot = ComponentTimeSeriesSnapshot(
        component_key='flotacion',
        windows=(one_hour, five_hours),
    )

    assert tuple(window.hours for window in snapshot.windows) == (1, 5)


def test_component_time_series_snapshot_rejects_duplicate_horizons() -> None:
    first = TimeSeriesWindowSnapshot(
        hours=1,
        start_utc=datetime(2026, 8, 15, 11, 0, tzinfo=UTC),
        end_utc=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        series={'a': [1]},
    )
    second = TimeSeriesWindowSnapshot(
        hours=1,
        start_utc=datetime(2026, 8, 15, 11, 0, tzinfo=UTC),
        end_utc=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        series={'b': [2]},
    )

    with pytest.raises(RuntimeDefinitionError, match='duplicate windows'):
        ComponentTimeSeriesSnapshot(
            component_key='flotacion',
            windows=(first, second),
        )


def test_component_state_snapshot_keeps_independent_subcomponent_states() -> None:
    snapshot = ComponentStateSnapshot(
        component_key='flotacion',
        states={
            'colectiva': ComponentProjectionState.STALE,
            'selectiva': ComponentProjectionState.CONSTRUCTION,
        },
    )

    assert snapshot.state('colectiva') is ComponentProjectionState.STALE
    assert snapshot.state('selectiva') is ComponentProjectionState.CONSTRUCTION
    assert snapshot.state('missing') is None
