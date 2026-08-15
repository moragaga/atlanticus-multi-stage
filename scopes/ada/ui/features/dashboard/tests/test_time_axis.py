from datetime import UTC, datetime, timedelta

import pytest

from ada.runtime.web import ComponentTimeSeriesSnapshot, TimeSeriesWindowSnapshot
from ada.ui.features.dashboard import TimeAxisBuilder, TimeAxisError, TimeSeriesSettings


def test_time_axis_uses_half_open_utc_window_without_storing_end_point() -> None:
    window = TimeSeriesWindowSnapshot(
        hours=1,
        start_utc=datetime(2026, 8, 15, 11, 0, tzinfo=UTC),
        end_utc=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        series={'ley': tuple(range(6))},
    )
    builder = TimeAxisBuilder(
        TimeSeriesSettings(step_seconds=600, display_timezone='America/Santiago')
    )

    hydrated = builder.build(window)

    assert len(hydrated.axis.utc) == 6
    assert hydrated.axis.utc[0] == window.start_utc
    assert hydrated.axis.utc[-1] == datetime(2026, 8, 15, 11, 50, tzinfo=UTC)
    assert window.end_utc not in hydrated.axis.utc


def test_time_axis_fall_back_disambiguates_repeated_chilean_clock_labels() -> None:
    window = TimeSeriesWindowSnapshot(
        hours=1,
        start_utc=datetime(2026, 4, 5, 2, 30, tzinfo=UTC),
        end_utc=datetime(2026, 4, 5, 3, 30, tzinfo=UTC),
        series={'ley': [1, 2]},
    )
    builder = TimeAxisBuilder(
        TimeSeriesSettings(step_seconds=1800, display_timezone='America/Santiago')
    )

    hydrated = builder.build(window)

    assert hydrated.axis.labels == (
        '2026-04-04 23:30:00',
        '2026-04-04 23:00:00',
    )

    extended = TimeSeriesWindowSnapshot(
        hours=2,
        start_utc=datetime(2026, 4, 5, 2, 30, tzinfo=UTC),
        end_utc=datetime(2026, 4, 5, 4, 30, tzinfo=UTC),
        series={'ley': [1, 2, 3, 4]},
    )
    hydrated_extended = builder.build(extended)

    assert hydrated_extended.axis.labels[0] == '2026-04-04 23:30:00 (UTC-03:00)'
    assert hydrated_extended.axis.labels[2] == '2026-04-04 23:30:00 (UTC-04:00)'


def test_time_axis_spring_forward_preserves_real_utc_spacing_and_skips_missing_local_hour() -> None:
    window = TimeSeriesWindowSnapshot(
        hours=1,
        start_utc=datetime(2026, 9, 6, 3, 30, tzinfo=UTC),
        end_utc=datetime(2026, 9, 6, 4, 30, tzinfo=UTC),
        series={'ley': [1, 2]},
    )
    builder = TimeAxisBuilder(
        TimeSeriesSettings(step_seconds=1800, display_timezone='America/Santiago')
    )

    hydrated = builder.build(window)

    assert hydrated.axis.labels == (
        '2026-09-05 23:30:00',
        '2026-09-06 01:00:00',
    )
    assert hydrated.axis.utc[1] - hydrated.axis.utc[0] == timedelta(seconds=1800)


def test_time_axis_rejects_series_length_that_does_not_match_window_and_step() -> None:
    window = TimeSeriesWindowSnapshot(
        hours=1,
        start_utc=datetime(2026, 8, 15, 11, 0, tzinfo=UTC),
        end_utc=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        series={'ley': [1, 2]},
    )
    builder = TimeAxisBuilder(
        TimeSeriesSettings(step_seconds=600, display_timezone='America/Santiago')
    )

    with pytest.raises(TimeAxisError, match='length does not match'):
        builder.build(window)


def test_time_axis_rejects_window_not_aligned_to_tool_step() -> None:
    window = TimeSeriesWindowSnapshot(
        hours=1,
        start_utc=datetime(2026, 8, 15, 11, 0, 5, tzinfo=UTC),
        end_utc=datetime(2026, 8, 15, 12, 0, 5, tzinfo=UTC),
        series={'ley': [1] * 6},
    )
    builder = TimeAxisBuilder(
        TimeSeriesSettings(step_seconds=600, display_timezone='America/Santiago')
    )

    with pytest.raises(TimeAxisError, match='must align to step_seconds'):
        builder.build(window)


def test_time_axis_builds_each_horizon_once_per_component_snapshot() -> None:
    snapshot = ComponentTimeSeriesSnapshot(
        component_key='flotacion',
        revision=2,
        windows=(
            TimeSeriesWindowSnapshot(
                hours=1,
                start_utc=datetime(2026, 8, 15, 11, 0, tzinfo=UTC),
                end_utc=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
                series={'a': [1] * 6, 'b': [2] * 6},
            ),
            TimeSeriesWindowSnapshot(
                hours=5,
                start_utc=datetime(2026, 8, 15, 7, 0, tzinfo=UTC),
                end_utc=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
                series={'c': [3] * 30},
            ),
        ),
    )
    builder = TimeAxisBuilder(
        TimeSeriesSettings(step_seconds=600, display_timezone='America/Santiago')
    )

    windows = builder.build_snapshot(snapshot)

    assert tuple(windows) == (1, 5)
    assert len(windows[1].axis.utc) == 6
    assert len(windows[5].axis.utc) == 30
