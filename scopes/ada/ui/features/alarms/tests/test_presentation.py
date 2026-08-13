from dash.development.base_component import Component

from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST, ToolScope
from ada.ui.components.state_wrapper import ComponentCover
from ada.ui.features.alarms.management_summary import (
    AlarmManagementSummarySegmentState,
    AlarmManagementSummaryTone,
    build_alarm_management_summary,
    create_alarm_management_summary_state,
)
from ada.ui.features.alarms.notifications import AlarmStatusState, build_alarm_status


def test_management_summary_owns_header_presentation_and_readiness() -> None:
    state = create_alarm_management_summary_state(
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
        segments=(
            AlarmManagementSummarySegmentState(
                'alarm_management_mine',
                ToolScope.MINE,
                'G3',
                60,
                AlarmManagementSummaryTone.ATTENTION,
            ),
            AlarmManagementSummarySegmentState(
                'alarm_management_plant',
                ToolScope.PLANT,
                'G1',
                45,
                AlarmManagementSummaryTone.CRITICAL,
            ),
        ),
    )

    component = build_alarm_management_summary(state, cover=ComponentCover.stale())
    wrapper = _require_by_class(component, 'ada-state-wrapper')
    segment = _require_by_class(component, 'ada-alarm-management-summary__segment')

    assert _prop(wrapper, 'data-ready-name') == 'alarm-management'
    assert _prop(wrapper, 'data-ready') == 'true'
    assert _prop(wrapper, 'data-cover') == 'stale'
    assert _prop(segment, 'data-scope') == 'mine'
    assert _prop(segment, 'data-tone') == 'attention'


def test_alarm_status_owns_header_presentation_and_readiness() -> None:
    component = build_alarm_status(
        AlarmStatusState(active_count=3, managed_count=2),
        cover=ComponentCover.construction(),
    )
    wrapper = _require_by_class(component, 'ada-state-wrapper')
    status = _require_by_class(component, 'ada-alarm-notifications-status')

    assert _prop(wrapper, 'data-ready-name') == 'alarm-status'
    assert _prop(wrapper, 'data-ready') == 'true'
    assert _prop(wrapper, 'data-cover') == 'construction'
    assert _prop(status, 'data-section-key') == 'alarm_status'
    assert _prop(status, 'data-scope') == 'global'


def _require_by_class(component: Component, class_name: str) -> Component:
    result = _find_by_class(component, class_name)
    if result is None:
        raise AssertionError(f'Component with class {class_name!r} was not found')
    return result


def _find_by_class(component: Component, class_name: str) -> Component | None:
    classes = getattr(component, 'className', '') or ''
    if class_name in classes.split():
        return component
    children = getattr(component, 'children', None)
    if children is None:
        return None
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if isinstance(child, Component):
            result = _find_by_class(child, class_name)
            if result is not None:
                return result
    return None


def _prop(component: Component, name: str):
    return component.to_plotly_json()['props'][name]
