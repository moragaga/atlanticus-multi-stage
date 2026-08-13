from pathlib import Path

import pytest

from ada.ui.features.alarms import AlarmDefinitionError
from ada.ui.features.alarms.dashboard import (
    AlarmBaselineDefinition,
    AlarmBaselineLayout,
    AlarmBaselineTarget,
    AlarmBaselineTargetKind,
    AlarmDashboardRouteDefinition,
    AlarmRouteTone,
    alarm_card_identity_attributes,
    alarm_geometry_scope_attributes,
    build_alarm_dashboard_route_layer,
    build_integrated_operations_alarm_baseline,
    build_process_alarm_baseline,
)
from ada.ui.framework.core import component_identity_attributes, slot_identity_attributes


def _props(component) -> dict[str, object]:
    return component.to_plotly_json()['props']


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


def test_route_definition_supports_same_point_and_origin_to_multiple_impacts() -> None:
    origin = AlarmBaselineTarget(AlarmBaselineTargetKind.COMPONENT, 'loading')
    same_point = AlarmDashboardRouteDefinition(
        route_key='same_point',
        card_key='alarm_1',
        origin=origin,
        impacts=(origin,),
        tone=AlarmRouteTone.CRITICAL,
    )
    span = AlarmDashboardRouteDefinition(
        route_key='span',
        card_key='alarm_2',
        origin=origin,
        impacts=(
            AlarmBaselineTarget(AlarmBaselineTargetKind.COMPONENT, 'flotation'),
            AlarmBaselineTarget(AlarmBaselineTargetKind.COMPONENT, 'port'),
        ),
        tone=AlarmRouteTone.ATTENTION,
    )

    assert same_point.impacts == (origin,)
    assert tuple(target.key for target in span.impacts) == ('flotation', 'port')


def test_route_definition_rejects_invalid_or_duplicate_impacts() -> None:
    origin = AlarmBaselineTarget(AlarmBaselineTargetKind.SLOT, 'center')

    with pytest.raises(AlarmDefinitionError, match='at least one impact'):
        AlarmDashboardRouteDefinition(
            route_key='process',
            card_key='alarm_1',
            origin=origin,
            impacts=(),
            tone=AlarmRouteTone.CRITICAL,
        )

    with pytest.raises(AlarmDefinitionError, match='duplicate impact targets'):
        AlarmDashboardRouteDefinition(
            route_key='process',
            card_key='alarm_1',
            origin=origin,
            impacts=(origin, origin),
            tone=AlarmRouteTone.CRITICAL,
        )


def test_route_layer_serializes_only_visual_target_identity() -> None:
    center = AlarmBaselineTarget(AlarmBaselineTargetKind.SLOT, 'center')
    route = build_alarm_dashboard_route_layer(
        AlarmDashboardRouteDefinition(
            route_key='process_center',
            card_key='process_alarm',
            origin=center,
            impacts=(center,),
            tone=AlarmRouteTone.CRITICAL,
        )
    )
    props = _props(route)

    assert props['data-ada-alarm-route'] == 'process_center'
    assert props['data-ada-alarm-route-card-key'] == 'process_alarm'
    assert props['data-ada-alarm-route-origin'] == 'slot:center'
    assert props['data-ada-alarm-route-impacts'] == 'slot:center'
    assert props['data-ada-alarm-route-tone'] == 'critical'


def test_dashboard_assets_keep_baseline_permanent_and_routes_clientside() -> None:
    resources = (
        Path(__file__).parents[1] / 'src' / 'ada' / 'ui' / 'features' / 'alarms' / 'resources'
    )
    baseline_css = (resources / 'css' / '20-dashboard-baseline.css').read_text(encoding='utf-8')
    route_css = (resources / 'css' / '30-dashboard-routes.css').read_text(encoding='utf-8')
    impact_css = (resources / 'css' / '40-impact.css').read_text(encoding='utf-8')
    geometry_js = (resources / 'js' / '10-dashboard-geometry.js').read_text(encoding='utf-8')
    routes_js = (resources / 'js' / '20-dashboard-routes.js').read_text(encoding='utf-8')

    assert '--ada-alarm-node-size: .75rem;' in baseline_css
    assert '--ada-alarm-node-glyph-size: .5rem;' in baseline_css
    assert 'height: .1875rem;' in baseline_css
    assert "data-ada-alarm-node-state='origin-impact'" in baseline_css
    assert '--ada-alarm-route-track-offset: 1.25rem;' in route_css
    assert 'stroke-width: .1rem;' in route_css
    assert "[data-ada-alarm-impact='active']" in impact_css
    assert 'ResizeObserver' in geometry_js
    assert 'MutationObserver' in geometry_js
    assert 'requestAnimationFrame' in geometry_js
    assert 'ResizeObserver' in routes_js
    assert 'requestAnimationFrame' in routes_js
    assert 'createElementNS' in routes_js
    assert 'data-ada-slot-key' in routes_js
    assert 'data-ada-component-key' in routes_js
    assert 'setInterval' not in routes_js
    assert 'fetch(' not in routes_js
