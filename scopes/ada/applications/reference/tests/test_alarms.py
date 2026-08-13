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
