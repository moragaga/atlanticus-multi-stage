from datetime import UTC, datetime, timedelta

import pytest

from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from ada.runtime.web import RuntimeSnapshot, SourceState
from ada.ui.shell.time_status import (
    build_ada_time_status,
    create_time_status_state,
    format_elapsed_time,
)


def _source_props(component):
    props = component.to_plotly_json()['props']
    sources = props['children'][0].to_plotly_json()['props']['children']
    return [source.to_plotly_json()['props'] for source in sources]


def test_elapsed_time_uses_ten_second_buckets_then_closed_units() -> None:
    assert format_elapsed_time(0) == 'hace menos de 10 segundos'
    assert format_elapsed_time(9) == 'hace menos de 10 segundos'
    assert format_elapsed_time(10) == 'hace más de 10 segundos'
    assert format_elapsed_time(59) == 'hace más de 50 segundos'
    assert format_elapsed_time(60) == 'hace más de 1 minuto'
    assert format_elapsed_time(3_600) == 'hace más de 1 hora'
    assert format_elapsed_time(86_400) == 'hace más de 1 día'

    with pytest.raises(ValueError):
        format_elapsed_time(-1)


def test_initial_render_marks_source_stale_at_exact_threshold() -> None:
    now = datetime(2026, 8, 13, 16, 0, tzinfo=UTC)
    snapshot = RuntimeSnapshot(
        revision='r1',
        loaded_at_utc=now,
        sources={
            'pi': SourceState.healthy(
                'pi',
                updated_at_utc=now - timedelta(seconds=300),
            ),
            'dispatch': SourceState.healthy(
                'dispatch',
                updated_at_utc=now - timedelta(seconds=599),
            ),
        },
    )
    component = build_ada_time_status(
        create_time_status_state(
            manifest=INTEGRATED_OPERATIONS_MANIFEST,
            snapshot=snapshot,
        ),
        now_utc=now,
    )
    pi, dispatch = _source_props(component)

    assert pi['data-source-freshness'] == 'stale'
    assert 'is-stale' in pi['className']
    assert dispatch['data-source-freshness'] == 'fresh'
    assert 'is-fresh' in dispatch['className']


def test_unhealthy_source_is_rendered_without_becoming_stale() -> None:
    now = datetime(2026, 8, 13, 16, 0, tzinfo=UTC)
    snapshot = RuntimeSnapshot(
        revision='r1',
        loaded_at_utc=now,
        sources={
            'pi': SourceState.error('pi'),
            'dispatch': SourceState.unavailable('dispatch'),
        },
    )
    component = build_ada_time_status(
        create_time_status_state(
            manifest=INTEGRATED_OPERATIONS_MANIFEST,
            snapshot=snapshot,
        ),
        now_utc=now,
    )
    pi, dispatch = _source_props(component)

    assert pi['data-source-freshness'] == 'unknown'
    assert dispatch['data-source-freshness'] == 'unknown'
    assert 'is-error' in pi['className']
    assert 'is-unavailable' in dispatch['className']
    assert pi['children'][2].to_plotly_json()['props']['children'] == 'Source error'
    assert dispatch['children'][2].to_plotly_json()['props']['children'] == 'Source unavailable'


def test_clock_uses_santiago_timezone_and_expected_format() -> None:
    now = datetime(2026, 8, 13, 16, 0, 5, tzinfo=UTC)
    snapshot = RuntimeSnapshot(
        revision='r1',
        loaded_at_utc=now,
        sources={
            'pi': SourceState.healthy('pi', updated_at_utc=now),
            'dispatch': SourceState.healthy('dispatch', updated_at_utc=now),
        },
    )
    component = build_ada_time_status(
        create_time_status_state(
            manifest=INTEGRATED_OPERATIONS_MANIFEST,
            snapshot=snapshot,
        ),
        now_utc=now,
    )
    children = component.to_plotly_json()['props']['children']
    clock_children = children[1].to_plotly_json()['props']['children']

    assert clock_children[2].to_plotly_json()['props']['children'] == '13-08-2026 12:00:05'


def test_initial_render_never_recovers_runtime_stale_state() -> None:
    now = datetime(2026, 8, 13, 16, 0, tzinfo=UTC)
    snapshot = RuntimeSnapshot(
        revision='r3',
        loaded_at_utc=now,
        sources={
            'pi': SourceState.healthy('pi', updated_at_utc=now, stale=True),
            'dispatch': SourceState.healthy('dispatch', updated_at_utc=now),
        },
    )
    component = build_ada_time_status(
        create_time_status_state(
            manifest=INTEGRATED_OPERATIONS_MANIFEST,
            snapshot=snapshot,
        ),
        now_utc=now,
    )
    pi, _ = _source_props(component)

    assert pi['data-source-freshness'] == 'stale'
    assert 'is-stale' in pi['className']
