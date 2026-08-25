from datetime import UTC, datetime

import pytest

from ada.runtime.component_stores import RuntimeComponentStoreRegistry, RuntimeComponentStoreSpec
from ada.runtime.delivery_cache import DeliveryChannel, DeliverySnapshot
from ada.runtime.delivery_collector import RuntimeDeliveryCollectorError, plan_channel_updates


def _registry() -> RuntimeComponentStoreRegistry:
    return RuntimeComponentStoreRegistry(
        tool_key='operaciones_integradas',
        components=(
            RuntimeComponentStoreSpec(
                component_key='global_indicators',
                wrapper_id='wrapper-global',
                latest_store_id='latest-global',
                timeseries_store_id='timeseries-global',
            ),
            RuntimeComponentStoreSpec(
                component_key='molienda',
                wrapper_id='wrapper-molienda',
                latest_store_id='latest-molienda',
                timeseries_store_id='timeseries-molienda',
            ),
        ),
    )


def _snapshot(revision: str, minute: int, payload: dict[str, object]) -> DeliverySnapshot:
    return DeliverySnapshot(
        revision=revision,
        published_at_utc=datetime(2026, 8, 25, 12, minute, tzinfo=UTC),
        payload=payload,
    )


def test_latest_first_snapshot_maps_present_destination_and_preserves_unmapped_component() -> None:
    plan = plan_channel_updates(
        channel=DeliveryChannel.LATEST,
        snapshot=_snapshot(
            'latest-a',
            0,
            {
                'destinations': {
                    'global_indicators': {
                        'produccion_total': {
                            'status': 'ok',
                            'value_kind': 'value',
                            'value': '66,00',
                        }
                    }
                }
            },
        ),
        registry=_registry(),
        current_control={'revision': None, 'published_at_utc': None},
        current_payloads=(
            {'state': 'unmapped', 'items': {}},
            {'state': 'unmapped', 'items': {}},
        ),
    )

    assert plan.control == {
        'revision': 'latest-a',
        'published_at_utc': '2026-08-25T12:00:00Z',
    }
    assert plan.component_payloads[0] == {
        'state': 'mapped',
        'items': {
            'produccion_total': {
                'status': 'ok',
                'value_kind': 'value',
                'value': '66,00',
            }
        },
    }
    assert plan.component_payloads[1] is None


def test_same_revision_produces_no_updates() -> None:
    plan = plan_channel_updates(
        channel=DeliveryChannel.LATEST,
        snapshot=_snapshot('latest-a', 0, {'destinations': {}}),
        registry=_registry(),
        current_control={
            'revision': 'latest-a',
            'published_at_utc': '2026-08-25T12:00:00Z',
        },
        current_payloads=(
            {'state': 'unmapped', 'items': {}},
            {'state': 'unmapped', 'items': {}},
        ),
    )

    assert plan.control is None
    assert plan.component_payloads == (None, None)


def test_new_revision_updates_only_component_whose_payload_changed() -> None:
    global_payload = {
        'state': 'mapped',
        'items': {'produccion_total': {'status': 'ok', 'value_kind': 'value', 'value': '66,00'}},
    }
    plan = plan_channel_updates(
        channel=DeliveryChannel.LATEST,
        snapshot=_snapshot(
            'latest-b',
            1,
            {
                'destinations': {
                    'global_indicators': global_payload['items'],
                    'molienda': {
                        'produccion_total': {
                            'status': 'ok',
                            'value_kind': 'value',
                            'value': '62,10',
                        }
                    },
                }
            },
        ),
        registry=_registry(),
        current_control={
            'revision': 'latest-a',
            'published_at_utc': '2026-08-25T12:00:00Z',
        },
        current_payloads=(global_payload, {'state': 'unmapped', 'items': {}}),
    )

    assert plan.control is not None
    assert plan.component_payloads[0] is None
    assert plan.component_payloads[1] == {
        'state': 'mapped',
        'items': {
            'produccion_total': {
                'status': 'ok',
                'value_kind': 'value',
                'value': '62,10',
            }
        },
    }


def test_older_worker_snapshot_cannot_roll_browser_back() -> None:
    current = {
        'revision': 'latest-b',
        'published_at_utc': '2026-08-25T12:01:00Z',
    }
    incoming = DeliverySnapshot(
        revision='latest-a',
        published_at_utc=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
        payload={'destinations': {}},
    )

    plan = plan_channel_updates(
        channel=DeliveryChannel.LATEST,
        snapshot=incoming,
        registry=_registry(),
        current_control=current,
        current_payloads=(
            {'state': 'unmapped', 'items': {}},
            {'state': 'unmapped', 'items': {}},
        ),
    )

    assert plan.control is None
    assert plan.component_payloads == (None, None)


def test_timeseries_snapshot_is_partitioned_by_explicit_window_destination() -> None:
    snapshot = _snapshot(
        'timeseries-a',
        0,
        {
            'destinations': {
                'global_indicators': ['produccion_total'],
                'molienda': ['produccion_total'],
            },
            'windows': [
                {
                    'destination': 'global_indicators',
                    'hours': 1,
                    'start_utc': '2026-08-25T11:00:00Z',
                    'end_utc': '2026-08-25T12:00:00Z',
                    'keys': ['produccion_total'],
                    'values': [[64.2, 65.4]],
                },
                {
                    'destination': 'molienda',
                    'hours': 1,
                    'start_utc': '2026-08-25T11:00:00Z',
                    'end_utc': '2026-08-25T12:00:00Z',
                    'keys': ['produccion_total'],
                    'values': [[60.1, 62.2]],
                },
            ],
        },
    )

    plan = plan_channel_updates(
        channel=DeliveryChannel.TIMESERIES,
        snapshot=snapshot,
        registry=_registry(),
        current_control={'revision': None, 'published_at_utc': None},
        current_payloads=(
            {'state': 'unmapped', 'windows': []},
            {'state': 'unmapped', 'windows': []},
        ),
    )

    assert plan.component_payloads[0]['keys'] == ['produccion_total']
    assert plan.component_payloads[0]['windows'][0]['destination'] == 'global_indicators'
    assert plan.component_payloads[1]['windows'][0]['destination'] == 'molienda'


def test_timeseries_window_without_destination_fails_closed() -> None:
    with pytest.raises(RuntimeDeliveryCollectorError, match='window destination'):
        plan_channel_updates(
            channel=DeliveryChannel.TIMESERIES,
            snapshot=_snapshot(
                'timeseries-a',
                0,
                {
                    'destinations': {'molienda': ['produccion_total']},
                    'windows': [{'hours': 1, 'keys': ['produccion_total'], 'values': [[1]]}],
                },
            ),
            registry=_registry(),
            current_control=None,
            current_payloads=(
                {'state': 'unmapped', 'windows': []},
                {'state': 'unmapped', 'windows': []},
            ),
        )
