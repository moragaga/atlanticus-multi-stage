from datetime import UTC, datetime

import pytest

from ada.runtime.web import (
    ComponentDataSnapshot,
    ComponentTimeSeriesSnapshot,
    TimeSeriesWindowSnapshot,
)
from ada.ui.features.dashboard import (
    ComponentProjectionDefinition,
    DashboardDefinitionError,
    DashboardToolConfiguration,
    TimeAxisBuilder,
    TimeSeriesProjectionDefinition,
    TimeSeriesSettings,
    build_component_bundle,
)


def test_time_series_settings_require_static_step_that_divides_one_hour() -> None:
    settings = TimeSeriesSettings(step_seconds=10, display_timezone='America/Santiago')

    assert settings.step_seconds == 10
    assert settings.display_timezone == 'America/Santiago'

    with pytest.raises(DashboardDefinitionError, match='divide one hour exactly'):
        TimeSeriesSettings(step_seconds=7, display_timezone='America/Santiago')


def test_time_series_settings_validate_timezone_without_hardcoding_chile() -> None:
    settings = TimeSeriesSettings(step_seconds=60, display_timezone='UTC')

    assert settings.display_timezone == 'UTC'

    with pytest.raises(DashboardDefinitionError, match='Unknown time-series display_timezone'):
        TimeSeriesSettings(step_seconds=60, display_timezone='Mars/Olympus_Mons')


def test_component_projection_supports_independent_horizons_per_series() -> None:
    projection = ComponentProjectionDefinition(
        component_key='flotacion',
        data=True,
        time_series=(
            TimeSeriesProjectionDefinition(key='recuperacion', hours=1),
            TimeSeriesProjectionDefinition(key='flujo', hours=5),
            TimeSeriesProjectionDefinition(key='tendencia', hours=24),
        ),
    )

    assert tuple(item.hours for item in projection.time_series) == (1, 5, 24)


def test_dashboard_configuration_requires_settings_only_when_time_series_are_declared() -> None:
    with pytest.raises(DashboardDefinitionError, match='require time-series settings'):
        DashboardToolConfiguration(
            components=(
                ComponentProjectionDefinition(
                    component_key='flotacion',
                    time_series=(TimeSeriesProjectionDefinition(key='ley', hours=1),),
                ),
            )
        )

    configuration = DashboardToolConfiguration(
        components=(ComponentProjectionDefinition(component_key='puerto', data=True),)
    )

    assert configuration.time_series is None


def test_component_bundle_keeps_missing_snapshot_distinct_from_explicit_none_payload_value() -> (
    None
):
    missing = build_component_bundle(component_key='flotacion')
    snapshot = ComponentDataSnapshot(
        component_key='flotacion',
        revision=1,
        payload={'ley': None},
    )
    available = build_component_bundle(component_key='flotacion', data_snapshot=snapshot)

    assert missing.data is None
    assert available.data is not None
    assert 'ley' in available.data
    assert available.data['ley'] is None


def test_component_bundle_hydrates_compact_time_series_snapshot_without_timestamp_arrays() -> None:
    snapshot = ComponentTimeSeriesSnapshot(
        component_key='flotacion',
        revision=1,
        windows=(
            TimeSeriesWindowSnapshot(
                hours=1,
                start_utc=datetime(2026, 8, 15, 11, 0, tzinfo=UTC),
                end_utc=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
                series={'ley': [1, 2, 3, 4, 5, 6]},
            ),
        ),
    )
    builder = TimeAxisBuilder(
        TimeSeriesSettings(step_seconds=600, display_timezone='America/Santiago')
    )
    windows = builder.build_snapshot(snapshot)

    bundle = build_component_bundle(
        component_key='flotacion',
        time_series_snapshot=snapshot,
        windows=windows,
    )

    assert bundle.time_series[1].series['ley'] == (1, 2, 3, 4, 5, 6)
    assert len(bundle.time_series[1].axis.utc) == 6
