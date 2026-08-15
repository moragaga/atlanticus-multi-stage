from datetime import UTC, datetime

import pytest

from ada.features.dashboard import (
    ComponentDataSnapshot,
    ComponentProjectionState,
    ComponentStateSnapshot,
    ComponentTimeSeriesSnapshot,
    DashboardStoreError,
    TimeSeriesWindowSnapshot,
    decode_component_data_snapshot,
    decode_component_state_snapshot,
    decode_component_time_series_snapshot,
    encode_component_data_snapshot,
    encode_component_state_snapshot,
    encode_component_time_series_snapshot,
)


def test_data_snapshot_round_trip_preserves_explicit_none_and_nested_json() -> None:
    snapshot = ComponentDataSnapshot(
        component_key='flotacion',
        payload={'ley': None, 'matrix': {'values': [1, 2, None]}},
    )

    encoded = encode_component_data_snapshot(snapshot)
    decoded = decode_component_data_snapshot(encoded)

    assert decoded.component_key == 'flotacion'
    assert decoded.payload['ley'] is None
    assert decoded.payload['matrix'] == {'values': [1, 2, None]}


def test_data_snapshot_encoder_rejects_non_json_runtime_values() -> None:
    snapshot = ComponentDataSnapshot(
        component_key='flotacion',
        payload={'invalid': object()},
    )

    with pytest.raises(DashboardStoreError, match='not JSON-compatible'):
        encode_component_data_snapshot(snapshot)


def test_time_series_snapshot_round_trip_keeps_compact_windows_without_timestamps() -> None:
    snapshot = ComponentTimeSeriesSnapshot(
        component_key='flotacion',
        windows=(
            TimeSeriesWindowSnapshot(
                hours=1,
                start_utc=datetime(2026, 8, 15, 11, 0, tzinfo=UTC),
                end_utc=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
                series={'ley': [1, None, 3, 4, 5, 6]},
            ),
        ),
    )

    encoded = encode_component_time_series_snapshot(snapshot)
    decoded = decode_component_time_series_snapshot(encoded)

    assert 'timestamps' not in encoded['windows'][0]
    assert decoded == snapshot


def test_state_snapshot_round_trip_uses_projection_state_value() -> None:
    snapshot = ComponentStateSnapshot(
        component_key='flotacion',
        state=ComponentProjectionState.STALE,
    )

    encoded = encode_component_state_snapshot(snapshot)
    decoded = decode_component_state_snapshot(encoded)

    assert encoded['state'] == 'stale'
    assert decoded == snapshot


def test_state_snapshot_decoder_rejects_unknown_state() -> None:
    with pytest.raises(DashboardStoreError, match='Unknown component projection state'):
        decode_component_state_snapshot({'component_key': 'flotacion', 'state': 'mystery'})
