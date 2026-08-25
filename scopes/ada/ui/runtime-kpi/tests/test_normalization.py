import json

import pytest

from ada.ui.framework.core import DisplayStatus
from ada.ui.runtime_kpi import (
    RuntimeKpiUiError,
    RuntimeKpiValueKind,
    decode_timeseries_store,
    normalize_latest_value,
)


def test_unmapped_store_normalizes_to_not_mapped() -> None:
    value = normalize_latest_value({'state': 'unmapped', 'items': {}}, kpi_key='produccion')

    assert value.status is DisplayStatus.NOT_MAPPED
    assert value.value_kind is None
    assert value.value is None


def test_mapped_store_missing_key_is_not_mapped() -> None:
    value = normalize_latest_value({'state': 'mapped', 'items': {}}, kpi_key='produccion')

    assert value.status is DisplayStatus.NOT_MAPPED


def test_latest_statuses_preserve_contract_semantics() -> None:
    store = {
        'state': 'mapped',
        'items': {
            'ready': {'status': 'ok', 'value_kind': 'value', 'value': '66,00'},
            'missing': {'status': 'missing', 'value_kind': None, 'value': None},
            'error': {'status': 'error', 'value_kind': 'value', 'value': None},
        },
    }

    ready = normalize_latest_value(store, kpi_key='ready')
    missing = normalize_latest_value(store, kpi_key='missing')
    error = normalize_latest_value(store, kpi_key='error')

    assert ready.status is DisplayStatus.OK
    assert ready.value_kind is RuntimeKpiValueKind.VALUE
    assert ready.value == '66,00'
    assert missing.status is DisplayStatus.EMPTY
    assert error.status is DisplayStatus.ERROR


def test_json_kind_is_validated_and_decoded_in_ui_normalization() -> None:
    payload = {'state': 'RUN', 'details': [1, 2]}
    store = {
        'state': 'mapped',
        'items': {
            'estado': {
                'status': 'ok',
                'value_kind': 'json',
                'value': json.dumps(payload),
            }
        },
    }

    value = normalize_latest_value(store, kpi_key='estado')

    assert value.status is DisplayStatus.OK
    assert value.value_kind is RuntimeKpiValueKind.JSON
    assert value.value == payload


def test_invalid_json_becomes_invalid_visual_state() -> None:
    store = {
        'state': 'mapped',
        'items': {
            'estado': {'status': 'ok', 'value_kind': 'json', 'value': '{invalid'},
        },
    }

    value = normalize_latest_value(store, kpi_key='estado')

    assert value.status is DisplayStatus.INVALID


def test_unknown_status_or_kind_becomes_invalid() -> None:
    bad_status = {
        'state': 'mapped',
        'items': {'x': {'status': 'wat', 'value_kind': 'value', 'value': 'x'}},
    }
    bad_kind = {
        'state': 'mapped',
        'items': {'x': {'status': 'ok', 'value_kind': 'binary', 'value': 'x'}},
    }

    assert normalize_latest_value(bad_status, kpi_key='x').status is DisplayStatus.INVALID
    assert normalize_latest_value(bad_kind, kpi_key='x').status is DisplayStatus.INVALID


def test_timeseries_store_preserves_explicit_step_and_window_scope() -> None:
    snapshot = decode_timeseries_store(
        {
            'state': 'mapped',
            'step_seconds': 120,
            'keys': ['produccion_total'],
            'windows': [
                {
                    'destination': 'component_a',
                    'hours': 1,
                    'start_utc': '2026-08-25T02:24:00Z',
                    'end_utc': '2026-08-25T03:24:00Z',
                    'keys': ['produccion_total'],
                    'values': [[64.2, 64.8, None, 65.4]],
                }
            ],
        }
    )

    assert snapshot is not None
    assert snapshot.step_seconds == 120
    assert snapshot.keys == ('produccion_total',)
    assert len(snapshot.windows) == 1
    window = snapshot.windows[0]
    assert window.destination == 'component_a'
    assert window.start_utc == '2026-08-25T02:24:00Z'
    assert window.end_utc == '2026-08-25T03:24:00Z'
    assert window.series('produccion_total') == (64.2, 64.8, None, 65.4)


def test_unmapped_timeseries_store_returns_none() -> None:
    assert decode_timeseries_store({'state': 'unmapped', 'windows': []}) is None


def test_invalid_timeseries_contract_fails_closed() -> None:
    with pytest.raises(RuntimeKpiUiError, match='step_seconds'):
        decode_timeseries_store(
            {
                'state': 'mapped',
                'step_seconds': 0,
                'keys': [],
                'windows': [],
            }
        )
