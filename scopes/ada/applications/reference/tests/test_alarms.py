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


def test_reference_exposes_route_semantics_and_all_process_geometry_variants() -> None:
    from ada.applications.reference.alarm_dashboard import (
        build_reference_alarm_dashboard_baselines,
    )

    component = build_reference_alarm_dashboard_baselines()
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

    assert [_prop(item, 'data-ada-alarm-baseline') for item in baselines] == [
        'integrated-operations',
        'integrated-operations',
        'process',
        'process',
        'process',
        'process',
    ]
    assert [_prop(item, 'data-ada-alarm-route-tone') for item in routes] == [
        'critical',
        'attention',
        'critical',
        'critical',
        'critical',
        'critical',
    ]
    assert len(scopes) == 6

    io_card_keys = [
        [
            _optional_prop(item, 'data-ada-alarm-card-key')
            for item in _walk(scope)
            if _optional_prop(item, 'data-ada-alarm-card-key') is not None
        ]
        for scope in scopes[:2]
    ]
    assert io_card_keys == [
        ['io_same_point_alarm'],
        [
            'io_general_mine_alarm',
            'io_loading_alarm',
            'io_transport_alarm',
            'io_crushing_alarm',
            'io_flotation_alarm',
            'io_port_alarm',
        ],
    ]

    process_scopes = scopes[2:]
    assert all(
        any(_optional_prop(item, 'data-ada-slot-key') == 'center' for item in _walk(scope))
        for scope in process_scopes
    )
    assert all(
        len(
            [
                item
                for item in _walk(scope)
                if _optional_prop(item, 'data-ada-alarm-card-key') is not None
            ]
        )
        == 6
        for scope in process_scopes
    )
    slot_sets = [
        {
            _optional_prop(item, 'data-ada-slot-key')
            for item in _walk(scope)
            if _optional_prop(item, 'data-ada-slot-key') is not None
        }
        for scope in process_scopes
    ]
    assert slot_sets == [
        {'left', 'center', 'right'},
        {'left', 'center'},
        {'center', 'right'},
        {'center'},
    ]


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
    assert 'width: min(13.5rem, 70%);' not in css


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
