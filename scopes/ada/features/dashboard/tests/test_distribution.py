from datetime import UTC, datetime

import pytest

from ada.features.dashboard import (
    DashboardStoreError,
    decode_component_data_snapshot,
    decode_component_state_snapshot,
    decode_component_time_series_snapshot,
    distribute_shared_snapshot,
)
from ada.runtime.web import SharedSnapshot, SnapshotChannel


def _revision() -> str:
    return '20260815210000123456'


def test_data_distribution_projects_aggregated_snapshot_by_component_key() -> None:
    snapshot = SharedSnapshot(
        revision=_revision(),
        payload={
            'components': {
                'flotacion': {'recovery': 87.2, 'optional': None},
                'molienda': {'power': 102},
            },
            'global_indicators': {'transportado': 198},
        },
    )

    result = distribute_shared_snapshot(
        snapshot,
        channel=SnapshotChannel.DATA,
        component_keys=('flotacion', 'molienda'),
    )

    assert decode_component_data_snapshot(result['flotacion']).payload == {
        'recovery': 87.2,
        'optional': None,
    }
    assert decode_component_data_snapshot(result['molienda']).payload == {'power': 102}


def test_missing_component_clears_only_that_store() -> None:
    snapshot = SharedSnapshot(
        revision=_revision(),
        payload={'components': {'flotacion': {'recovery': 87.2}}},
    )

    result = distribute_shared_snapshot(
        snapshot,
        channel=SnapshotChannel.DATA,
        component_keys=('flotacion', 'molienda'),
    )

    assert result['flotacion'] is not None
    assert result['molienda'] is None


def test_time_series_distribution_keeps_compact_windows_without_timestamp_arrays() -> None:
    snapshot = SharedSnapshot(
        revision=_revision(),
        payload={
            'components': {
                'flotacion': {
                    'windows': [
                        {
                            'hours': 1,
                            'start_utc': '2026-08-15T20:00:00Z',
                            'end_utc': '2026-08-15T21:00:00Z',
                            'series': {'recovery': [1, 2, None, 4, 5, 6]},
                        }
                    ]
                }
            }
        },
    )

    result = distribute_shared_snapshot(
        snapshot,
        channel=SnapshotChannel.TIME_SERIES,
        component_keys=('flotacion',),
    )

    decoded = decode_component_time_series_snapshot(result['flotacion'])
    assert decoded.windows[0].start_utc == datetime(2026, 8, 15, 20, tzinfo=UTC)
    assert decoded.windows[0].end_utc == datetime(2026, 8, 15, 21, tzinfo=UTC)
    assert decoded.windows[0].series['recovery'] == (1, 2, None, 4, 5, 6)
    assert 'timestamps' not in result['flotacion']['windows'][0]


def test_status_distribution_preserves_subcomponent_state_isolation() -> None:
    snapshot = SharedSnapshot(
        revision=_revision(),
        payload={
            'components': {
                'flotacion': {'colectiva': 'stale', 'selectiva': 'construction'},
                'molienda': {'molienda': 'ready'},
            },
            'sources': {'pi': {'updated_at_utc': '2026-08-15T21:00:00Z'}},
        },
    )

    result = distribute_shared_snapshot(
        snapshot,
        channel=SnapshotChannel.STATUS,
        component_keys=('flotacion', 'molienda'),
    )

    flotacion = decode_component_state_snapshot(result['flotacion'])
    assert flotacion.state('colectiva').value == 'stale'
    assert flotacion.state('selectiva').value == 'construction'
    assert decode_component_state_snapshot(result['molienda']).state('molienda').value == 'ready'


def test_distribution_rejects_snapshot_without_components_envelope() -> None:
    snapshot = SharedSnapshot(revision=_revision(), payload={'flotacion': {'recovery': 87.2}})

    with pytest.raises(DashboardStoreError, match='requires components mapping'):
        distribute_shared_snapshot(
            snapshot,
            channel=SnapshotChannel.DATA,
            component_keys=('flotacion',),
        )
