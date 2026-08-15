from pathlib import Path

from dash.development.base_component import Component

from ada.applications.reference.alarms import (
    build_reference_alarm_management_summary,
    build_reference_alarm_status,
)
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST


def test_reference_alarm_header_presentations_preserve_existing_states() -> None:
    management = build_reference_alarm_management_summary(INTEGRATED_OPERATIONS_MANIFEST)
    status = build_reference_alarm_status()

    management_wrapper = _require_by_class(management, 'ada-state-wrapper')
    status_wrapper = _require_by_class(status, 'ada-state-wrapper')

    assert _prop(management_wrapper, 'data-ready-name') == 'alarm-management'
    assert _prop(management_wrapper, 'data-cover') == 'stale'
    assert _prop(status_wrapper, 'data-ready-name') == 'alarm-status'
    assert _prop(status_wrapper, 'data-cover') == 'construction'


def _require_by_class(component: Component, class_name: str) -> Component:
    classes = getattr(component, 'className', '') or ''
    if class_name in classes.split():
        return component
    children = getattr(component, 'children', None)
    if children is None:
        raise AssertionError(f'Component with class {class_name!r} was not found')
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if not isinstance(child, Component):
            continue
        try:
            return _require_by_class(child, class_name)
        except AssertionError:
            continue
    raise AssertionError(f'Component with class {class_name!r} was not found')


def _prop(component: Component, name: str):
    return component.to_plotly_json()['props'][name]


def test_alarm_header_ownership_is_not_exposed_by_header_shell() -> None:
    import ada.ui.shell.header as header

    for legacy_name in (
        'AlarmManagementSegmentState',
        'AlarmManagementState',
        'AlarmStatusState',
        'HeaderTone',
        'build_alarm_management',
        'build_alarm_status',
    ):
        assert not hasattr(header, legacy_name)


def test_reference_exposes_only_interactive_alarm_players() -> None:
    from ada.applications.reference.alarm_dashboard import build_reference_alarm_interaction

    component = build_reference_alarm_interaction()
    baselines = [
        item
        for item in _walk(component)
        if _optional_prop(item, 'data-ada-alarm-baseline') is not None
    ]
    routes = [
        item
        for item in _walk(component)
        if _optional_prop(item, 'data-ada-alarm-route') is not None
    ]
    scopes = [
        item
        for item in _walk(component)
        if _optional_prop(item, 'data-ada-alarm-geometry-scope') == 'true'
    ]

    assert len(scopes) == 2
    assert len(routes) == 2
    assert [_prop(item, 'data-ada-alarm-baseline') for item in baselines] == [
        'integrated-operations',
        'process',
    ]

    io_player, process_player = scopes
    for scope in (io_player, process_player):
        assert _prop(scope, 'data-ada-alarm-presentation-scope') == 'true'
        assert _prop(scope, 'data-ada-alarm-interaction') == 'interactive'
        assert _prop(scope, 'data-ada-alarm-trace-dwell-ms') == '15000'
        assert _optional_prop(scope, 'data-ada-alarm-visibility-strategy') is None

    io_events = [
        item
        for item in _walk(io_player)
        if _optional_prop(item, 'data-ada-alarm-event-id') is not None
    ]
    process_events = [
        item
        for item in _walk(process_player)
        if _optional_prop(item, 'data-ada-alarm-event-id') is not None
    ]
    assert len(io_events) == 6
    assert len(process_events) == 6
    loading = next(
        item for item in io_events if _prop(item, 'data-ada-alarm-event-id') == 'io-player-load-001'
    )
    flotation = next(
        item
        for item in io_events
        if _prop(item, 'data-ada-alarm-event-id') == 'io-player-flotation-001'
    )
    assert _prop(loading, 'data-ada-alarm-route-destinations') == (
        'component:flotation|component:fluid_transport|component:port'
    )
    assert _prop(loading, 'data-ada-alarm-affected-targets') == (
        'subcomponent:flotation_selective|'
        'subcomponent:fluid_transport_subcomponent_2|'
        'subcomponent:port_subcomponent_2'
    )
    assert _prop(flotation, 'data-ada-alarm-affected-targets') == (
        'subcomponent:grinding_subcomponent_2|component:flotation'
    )
    assert all(_prop(event, 'data-ada-alarm-placement-key') for event in io_events)
    assert all(_prop(event, 'data-ada-alarm-placement-key') for event in process_events)
    assert all(
        _prop(event, 'data-ada-alarm-route-destinations') == 'slot:center'
        for event in process_events
    )
    assert all(
        _prop(event, 'data-ada-alarm-affected-targets') == 'slot:center' for event in process_events
    )
    process_components = {
        _optional_prop(item, 'data-ada-component-key')
        for item in _walk(process_player)
        if (_optional_prop(item, 'data-ada-component-key') or '').startswith('process_')
    }
    assert process_components == set()

    io_lanes = [
        item
        for item in _walk(io_player)
        if 'reference-ada__alarm-component-lane'
        in (_optional_prop(item, 'className') or '').split()
    ]
    assert [_prop(item, 'data-ada-component-key') for item in io_lanes] == [
        'general_mine',
        'loading',
        'transport',
        'crushing_stmg',
        'stock_chacay',
        'grinding',
        'flotation',
        'fluid_transport',
        'port',
    ]
    assert [
        len(
            [
                item
                for item in _walk(lane)
                if 'reference-ada__alarm-subcomponent-card'
                in (_optional_prop(item, 'className') or '').split()
            ]
        )
        for lane in io_lanes
    ] == [1, 2, 3, 2, 1, 3, 2, 3, 2]


def test_reference_alarm_static_examples_are_removed() -> None:
    from ada.applications.reference import alarm_dashboard

    for name in (
        '_build_integrated_operations_same_point_reference',
        '_build_integrated_operations_span_reference',
        '_build_process_reference',
        '_build_static_process_alarm_grid',
    ):
        assert not hasattr(alarm_dashboard, name)


def test_reference_alarm_harness_separates_baseline_from_card_and_body_frames() -> None:
    from ada.applications.reference import alarm_dashboard

    css_path = Path(alarm_dashboard.__file__).parent / 'resources' / 'css' / '00-reference.css'
    css = css_path.read_text(encoding='utf-8')

    assert 'padding-block: .75rem;' in css
    assert 'padding-inline: var(--reference-alarm-frame-padding);' in css
    assert '.reference-ada__alarm-io-placement-grid,' in css
    assert '.reference-ada__alarm-io-grid {' in css
    assert 'grid-template-columns: var(--reference-alarm-io-columns);' in css
    assert '.reference-ada__alarm-process-placement-grid {' in css
    assert 'grid-template-columns: repeat(6, minmax(0, 1fr));' in css
    assert '--reference-alarm-io-columns: repeat(9, minmax(0, 1fr));' in css
    assert '.reference-ada__alarm-component-lane {' in css
    assert '.reference-ada__alarm-subcomponent-card {' in css
    assert '.reference-ada__alarm-target--component {' not in css
    assert '.reference-ada__alarm-component-stack {' not in css
    assert '.reference-ada__alarm-io-double {' not in css
    assert '.reference-ada__alarm-process-component-stack {' not in css
    assert '[data-ada-alarm-process-queue]\n    > [data-ada-alarm-event-id]' in css
    assert 'grid-row: 1;' in css
    assert 'var(--ada-alarm-card-color, #BDBDBD)' not in css
    assert 'width: min(13.5rem, 70%);' not in css
    assert '.reference-ada__alarm-process-variants' not in css
    assert '.reference-ada__alarm-example-grid' not in css


def _walk(component: Component):
    yield component
    children = getattr(component, 'children', None)
    if children is None:
        return
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if isinstance(child, Component):
            yield from _walk(child)


def _optional_prop(component: Component, name: str):
    return component.to_plotly_json()['props'].get(name)
