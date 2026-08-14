from pathlib import Path

import pytest

from ada.ui.features.alarms import AlarmDefinitionError
from ada.ui.features.alarms.dashboard import (
    AlarmBaselineDefinition,
    AlarmBaselineLayout,
    AlarmBaselineTarget,
    AlarmBaselineTargetKind,
    AlarmDashboardRouteDefinition,
    AlarmPresentationInteraction,
    AlarmRouteTone,
    AlarmVisibilityStrategy,
    alarm_card_identity_attributes,
    alarm_card_presentation_attributes,
    alarm_geometry_scope_attributes,
    alarm_presentation_scope_attributes,
    alarm_queue_lane_attributes,
    alarm_visibility_scope_attributes,
    build_alarm_dashboard_route_layer,
    build_integrated_operations_alarm_baseline,
    build_process_alarm_baseline,
)
from ada.ui.framework.core import component_identity_attributes, slot_identity_attributes


def _props(component) -> dict[str, object]:
    return component.to_plotly_json()['props']


def _route_definition(
    *,
    event_id: str = 'event-001',
    assignment_key: str = 'component:loading',
    card_key: str = 'alarm_1',
    tone: AlarmRouteTone = AlarmRouteTone.CRITICAL,
) -> AlarmDashboardRouteDefinition:
    origin = AlarmBaselineTarget(AlarmBaselineTargetKind.COMPONENT, 'loading')
    return AlarmDashboardRouteDefinition(
        event_id=event_id,
        assignment_key=assignment_key,
        card_key=card_key,
        origin=origin,
        impacts=(origin,),
        tone=tone,
    )


def test_integrated_operations_baseline_targets_components_in_declared_order() -> None:
    definition = AlarmBaselineDefinition.integrated_operations(
        ('general_mine', 'loading', 'transport')
    )

    assert definition.layout is AlarmBaselineLayout.INTEGRATED_OPERATIONS
    assert tuple(target.kind for target in definition.targets) == (
        AlarmBaselineTargetKind.COMPONENT,
        AlarmBaselineTargetKind.COMPONENT,
        AlarmBaselineTargetKind.COMPONENT,
    )
    assert tuple(target.key for target in definition.targets) == (
        'general_mine',
        'loading',
        'transport',
    )


def test_process_baseline_targets_only_center_slot() -> None:
    definition = AlarmBaselineDefinition.process()

    assert definition.layout is AlarmBaselineLayout.PROCESS
    assert len(definition.targets) == 1
    assert definition.targets[0].kind is AlarmBaselineTargetKind.SLOT
    assert definition.targets[0].key == 'center'


def test_baseline_rejects_duplicate_and_invalid_targets() -> None:
    with pytest.raises(AlarmDefinitionError, match='duplicate targets'):
        AlarmBaselineDefinition.integrated_operations(('grinding', 'grinding'))

    with pytest.raises(AlarmDefinitionError, match='Invalid alarm target key'):
        AlarmBaselineDefinition.integrated_operations(('Grinding Card',))


def test_dom_contract_exposes_stable_scope_component_slot_and_alarm_card_attributes() -> None:
    assert alarm_geometry_scope_attributes() == {'data-ada-alarm-geometry-scope': 'true'}
    assert component_identity_attributes('grinding') == {'data-ada-component-key': 'grinding'}
    assert slot_identity_attributes('center') == {'data-ada-slot-key': 'center'}
    assert alarm_card_identity_attributes('alarm_1') == {'data-ada-alarm-card-key': 'alarm_1'}


def test_baseline_presentation_preserves_final_node_boxes_and_glyph_slots() -> None:
    integrated = build_integrated_operations_alarm_baseline(('grinding', 'flotation'))
    process = build_process_alarm_baseline()

    integrated_props = _props(integrated)
    process_props = _props(process)
    integrated_nodes = integrated_props['children'][1:]
    process_nodes = process_props['children'][1:]

    assert integrated_props['data-ada-alarm-baseline'] == 'integrated-operations'
    assert process_props['data-ada-alarm-baseline'] == 'process'
    assert tuple(_props(node)['data-ada-alarm-target-key'] for node in integrated_nodes) == (
        'grinding',
        'flotation',
    )
    assert _props(process_nodes[0])['data-ada-alarm-target-kind'] == 'slot'
    assert _props(process_nodes[0])['data-ada-alarm-target-key'] == 'center'
    assert all(_props(node)['data-ada-alarm-positioned'] == 'false' for node in integrated_nodes)
    assert all(_props(node)['data-ada-alarm-node-state'] == 'neutral' for node in integrated_nodes)
    assert all(len(_props(node)['children']) == 3 for node in integrated_nodes)


def test_route_definition_keeps_event_identity_separate_from_assignment() -> None:
    origin = AlarmBaselineTarget(AlarmBaselineTargetKind.COMPONENT, 'loading')
    span = AlarmDashboardRouteDefinition(
        event_id='event-abc-123',
        assignment_key='component:loading',
        card_key='alarm_2',
        origin=origin,
        impacts=(
            AlarmBaselineTarget(AlarmBaselineTargetKind.COMPONENT, 'flotation'),
            AlarmBaselineTarget(AlarmBaselineTargetKind.COMPONENT, 'port'),
        ),
        tone=AlarmRouteTone.ATTENTION,
    )

    assert span.event_id == 'event-abc-123'
    assert span.assignment_key == 'component:loading'
    assert tuple(target.key for target in span.impacts) == ('flotation', 'port')


def test_route_definition_rejects_invalid_or_duplicate_impacts() -> None:
    origin = AlarmBaselineTarget(AlarmBaselineTargetKind.SLOT, 'center')

    with pytest.raises(AlarmDefinitionError, match='at least one impact'):
        AlarmDashboardRouteDefinition(
            event_id='event-001',
            assignment_key='process_slot_1',
            card_key='alarm_1',
            origin=origin,
            impacts=(),
            tone=AlarmRouteTone.CRITICAL,
        )

    with pytest.raises(AlarmDefinitionError, match='duplicate impact targets'):
        AlarmDashboardRouteDefinition(
            event_id='event-001',
            assignment_key='process_slot_1',
            card_key='alarm_1',
            origin=origin,
            impacts=(origin, origin),
            tone=AlarmRouteTone.CRITICAL,
        )


def test_card_presentation_serializes_event_assignment_tone_and_route_geometry() -> None:
    definition = _route_definition(tone=AlarmRouteTone.ATTENTION)

    attributes = alarm_card_presentation_attributes(definition, distributed=True)

    assert attributes['data-ada-alarm-card-key'] == 'alarm_1'
    assert attributes['data-ada-alarm-event-id'] == 'event-001'
    assert attributes['data-ada-alarm-assignment-key'] == 'component:loading'
    assert attributes['data-ada-alarm-card-tone'] == 'attention'
    assert attributes['data-ada-alarm-route-origin'] == 'component:loading'
    assert attributes['data-ada-alarm-route-impacts'] == 'component:loading'
    assert attributes['data-ada-alarm-distributed'] == 'true'
    assert attributes['data-ada-alarm-selected'] == 'false'


def test_route_layer_can_be_dynamic_or_seeded_for_static_reference() -> None:
    dynamic = _props(build_alarm_dashboard_route_layer())
    seeded = _props(build_alarm_dashboard_route_layer(_route_definition()))

    assert dynamic['data-ada-alarm-route'] == 'active'
    assert dynamic['data-ada-alarm-route-state'] == 'idle'
    assert 'data-ada-alarm-route-event-id' not in dynamic
    assert seeded['data-ada-alarm-route-event-id'] == 'event-001'
    assert seeded['data-ada-alarm-route-card-key'] == 'alarm_1'
    assert seeded['data-ada-alarm-route-state'] == 'active'
    assert seeded['data-ada-alarm-route-replay'] == '1'


def test_presentation_and_visibility_attributes_require_explicit_timing() -> None:
    assert alarm_presentation_scope_attributes(
        trace_dwell_ms=120_000,
        interaction=AlarmPresentationInteraction.INTERACTIVE,
    ) == {
        'data-ada-alarm-presentation-scope': 'true',
        'data-ada-alarm-trace-dwell-ms': '120000',
        'data-ada-alarm-interaction': 'interactive',
    }
    assert (
        alarm_presentation_scope_attributes(
            trace_dwell_ms=120_000,
            interaction=AlarmPresentationInteraction.VIEW_ONLY,
        )['data-ada-alarm-interaction']
        == 'view-only'
    )
    assert alarm_visibility_scope_attributes(
        AlarmVisibilityStrategy.PROCESS,
        rotation_interval_ms=150_000,
        distributed_interval_ms=90_000,
    ) == {
        'data-ada-alarm-visibility-strategy': 'process',
        'data-ada-alarm-rotation-interval-ms': '150000',
        'data-ada-alarm-distributed-interval-ms': '90000',
    }
    assert alarm_queue_lane_attributes('loading', interval_ms=120_000) == {
        'data-ada-alarm-queue-lane': 'loading',
        'data-ada-alarm-queue-interval-ms': '120000',
    }

    with pytest.raises(AlarmDefinitionError, match='trace dwell'):
        alarm_presentation_scope_attributes(
            trace_dwell_ms=0,
            interaction=AlarmPresentationInteraction.INTERACTIVE,
        )


def test_dashboard_assets_animate_trace_and_impact_without_backend_polling() -> None:
    resources = (
        Path(__file__).parents[1] / 'src' / 'ada' / 'ui' / 'features' / 'alarms' / 'resources'
    )
    baseline_css = (resources / 'css' / '20-dashboard-baseline.css').read_text(encoding='utf-8')
    route_css = (resources / 'css' / '30-dashboard-routes.css').read_text(encoding='utf-8')
    presentation_css = (resources / 'css' / '50-presentation.css').read_text(encoding='utf-8')
    geometry_js = (resources / 'js' / '10-dashboard-geometry.js').read_text(encoding='utf-8')
    routes_js = (resources / 'js' / '20-dashboard-routes.js').read_text(encoding='utf-8')
    presentation_js = (resources / 'js' / '30-dashboard-presentation.js').read_text(
        encoding='utf-8'
    )
    scheduling_js = (resources / 'js' / '40-dashboard-scheduling.js').read_text(encoding='utf-8')

    assert '--ada-alarm-node-size: .75rem;' in baseline_css
    assert 'height: .1875rem;' in baseline_css
    assert '--ada-alarm-route-track-offset: 1.25rem;' in route_css
    assert 'stroke-width: .1rem;' in route_css
    assert '@keyframes adaAlarmFlow' in route_css
    assert '.ada-alarm-dashboard-route__impact-path' in route_css
    assert "data-ada-alarm-card-tone='critical'" in presentation_css
    assert "data-ada-alarm-selected='true'" not in presentation_css
    assert 'ResizeObserver' in geometry_js
    assert 'requestAnimationFrame' in geometry_js
    assert 'FLOW_SPEED_PX_PER_SECOND = 520' in routes_js
    assert 'getTotalLength' in routes_js
    assert 'adaAlarmFlow' in routes_js
    assert 'nextAnimationFrame' in routes_js
    assert 'prefers-reduced-motion: reduce' in routes_js
    assert 'createImpactPath' in routes_js
    assert 'geometry.entry' in routes_js
    assert 'geometry.connector' in routes_js
    assert 'observeResizeElement' in routes_js
    assert 'geometrySizes' in routes_js
    assert 'element.animate' not in routes_js
    assert "record.target.closest('.ada-alarm-dashboard-route__svg')" in routes_js
    assert 'ada-alarm-dashboard-route__context-path' in routes_js
    assert "COMPLETE_EVENT = 'ada:alarm-route-complete'" in routes_js
    assert 'effectiveEventCount() === 1' in presentation_js
    assert 'INTERACTIVE_SELECTOR' in presentation_js
    assert 'this.activateCard(card, true);' in presentation_js
    assert 'window.setTimeout' in presentation_js
    assert 'else if (this.timer !== null)' in presentation_js
    assert 'adaAlarmTraceDwellMs' in presentation_js
    assert 'handleRouteComplete' in presentation_js
    assert 'distributed.length >= 2' in scheduling_js
    assert 'if (this.normalTimer !== null)' in scheduling_js
    assert 'if (this.distributedTimer !== null)' in scheduling_js
    assert 'const normalCapacity = reserved ? 5 : 6;' in scheduling_js
    assert 'edgeOrder(capacity)' in scheduling_js
    assert "card.style.gridRow = '1';" in scheduling_js
    for javascript in (routes_js, presentation_js, scheduling_js):
        assert 'setInterval' not in javascript
        assert 'fetch(' not in javascript
