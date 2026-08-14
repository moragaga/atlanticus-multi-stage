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


def test_dashboard_assets_keep_white_context_and_use_one_sequential_player() -> None:
    resources = (
        Path(__file__).parents[1] / 'src' / 'ada' / 'ui' / 'features' / 'alarms' / 'resources'
    )
    baseline_css = (resources / 'css' / '20-dashboard-baseline.css').read_text(encoding='utf-8')
    route_css = (resources / 'css' / '30-dashboard-routes.css').read_text(encoding='utf-8')
    presentation_css = (resources / 'css' / '50-presentation.css').read_text(encoding='utf-8')
    geometry_js = (resources / 'js' / '10-dashboard-geometry.js').read_text(encoding='utf-8')
    routes_js = (resources / 'js' / '20-dashboard-routes.js').read_text(encoding='utf-8')
    js_list = (resources / 'js' / 'js.list').read_text(encoding='utf-8').splitlines()

    assert '--ada-alarm-node-size: .75rem;' in baseline_css
    assert 'height: .1875rem;' in baseline_css
    assert '--ada-alarm-route-track-offset: 1.25rem;' in route_css
    assert '--ada-alarm-route-critical-color: #C82333;' in route_css
    assert '--ada-alarm-route-attention-color: #E0A800;' in route_css
    assert '--ada-alarm-route-context-color: #F4F4F4;' in route_css
    assert 'stroke: var(--ada-alarm-route-context-color);' in route_css
    assert '@keyframes adaAlarmFlow' not in route_css
    assert '.ada-alarm-dashboard-route__impact-path' in route_css
    assert "data-ada-alarm-card-tone='critical'" in presentation_css
    assert "data-ada-alarm-selected='true'" not in presentation_css
    assert 'ResizeObserver' in geometry_js
    assert 'requestAnimationFrame' in geometry_js

    assert 'MOTION_SCOPE_WIDTHS_PER_SECOND = 0.2' in routes_js
    assert 'MIN_MOTION_SPEED_PX_PER_SECOND = 160' in routes_js
    assert 'MAX_MOTION_SPEED_PX_PER_SECOND = 960' in routes_js
    assert 'PREFIX_GAP_PX = 24' in routes_js
    assert 'PREFIX_GAP_RATIO = 0.08' in routes_js
    assert 'IMPACT_MIN_DURATION_MS = 1_600' in routes_js
    assert 'IMPACT_MAX_DURATION_MS = 2_400' in routes_js
    assert 'SHARED_TRUNK_DURATION_MS' not in routes_js
    assert 'FAN_OUT_DURATION_MS' not in routes_js
    assert 'IMPACT_DURATION_MS' not in routes_js
    assert 'FLOW_SPEED_PX_PER_SECOND' not in routes_js
    assert 'MIN_FLOW_DURATION_MS' not in routes_js
    assert 'DEFAULT_DWELL_MS = 15_000' in routes_js

    assert 'specification.geometry.contextSegments.forEach' in routes_js
    assert 'specification.geometry.contextPath' not in routes_js
    assert 'sharedTrunk,' in routes_js
    assert 'originLeg,' in routes_js
    assert 'impactLegs,' in routes_js
    assert 'contextSegments: [' in routes_js
    assert 'createImpactPaths' in routes_js
    assert 'createImpactPath(' not in routes_js
    assert 'return [leftPath, rightPath];' in routes_js

    assert 'startMotion(' in routes_js
    assert 'beginMotionPhase(' in routes_js
    assert 'tickMotion(timestamp)' in routes_js
    assert 'prepareMotionStroke(' in routes_js
    assert 'commitMotionStroke(' in routes_js
    assert 'finishMotion()' in routes_js
    assert 'cancelMotion(reason)' in routes_js
    assert "phase: 'shared-trunk'" in routes_js
    assert "this.beginMotionPhase('fan-out')" in routes_js
    assert "this.beginMotionPhase('impact')" in routes_js
    assert '`impact-leg:${target.kind}:${target.key}`' in routes_js
    assert "const side = pathIndex === 0 ? 'left' : 'right';" in routes_js
    assert (
        'this.motion.phaseDurationMs = this.impactPhaseDuration(this.motion.strokes);' in routes_js
    )

    speed_start = routes_js.index('        motionSpeed() {')
    speed_end = routes_js.index('\n        startMotion(', speed_start)
    speed_body = routes_js[speed_start:speed_end]
    assert 'getBoundingClientRect().width' in speed_body
    assert 'width * MOTION_SCOPE_WIDTHS_PER_SECOND' in speed_body
    assert 'MAX_MOTION_SPEED_PX_PER_SECOND' in speed_body
    assert 'MIN_MOTION_SPEED_PX_PER_SECOND' in speed_body

    stroke_start = routes_js.index('        prepareMotionStroke(')
    stroke_end = routes_js.index('\n        impactPhaseDuration(', stroke_start)
    stroke_body = routes_js[stroke_start:stroke_end]
    assert "path.style.visibility = 'hidden'" in stroke_body
    assert "path.style.opacity = '0'" in stroke_body
    assert "path.style.strokeLinecap = 'butt'" in stroke_body
    assert "path.style.strokeDashoffset = '0'" in stroke_body
    assert 'container.appendChild(path)' in stroke_body
    assert 'path.getTotalLength()' in stroke_body
    assert 'Math.max(PREFIX_GAP_PX, length * PREFIX_GAP_RATIO)' in stroke_body
    assert 'const gapLength = length + guard;' in stroke_body
    assert 'path.style.strokeDasharray = `0 ${gapLength}`' in stroke_body
    assert 'drawLength' not in stroke_body

    impact_duration_start = routes_js.index('        impactPhaseDuration(')
    impact_duration_end = routes_js.index('\n        easeImpactProgress(', impact_duration_start)
    impact_duration_body = routes_js[impact_duration_start:impact_duration_end]
    assert 'Math.max(...strokes.map((stroke) => stroke.length))' in impact_duration_body
    assert '(longest / this.motion.speed) * 1000' in impact_duration_body
    assert 'IMPACT_MIN_DURATION_MS' in impact_duration_body
    assert 'IMPACT_MAX_DURATION_MS' in impact_duration_body

    reveal_start = routes_js.index('        revealMotionStroke(')
    reveal_end = routes_js.index('\n        tickMotion(', reveal_start)
    reveal_body = routes_js[reveal_start:reveal_end]
    assert '`${clamped} ${stroke.gapLength}`' in reveal_body
    assert "stroke.path.style.visibility = 'visible'" in reveal_body
    assert "stroke.path.style.opacity = '1'" in reveal_body
    assert 'strokeDashoffset' not in reveal_body

    tick_start = routes_js.index('        tickMotion(timestamp) {')
    tick_end = routes_js.index('\n        commitMotionStroke(', tick_start)
    tick_body = routes_js[tick_start:tick_end]
    assert 'elapsedSeconds * motion.speed' in tick_body
    assert "motion.phase === 'impact'" in tick_body
    assert 'this.easeImpactProgress(elapsedMs / motion.phaseDurationMs)' in tick_body
    assert 'Math.min(stroke.length, distance)' in tick_body
    assert 'stroke.length * impactProgress' in tick_body
    assert 'this.revealMotionStroke(stroke, visibleLength)' in tick_body
    assert 'visibleLength >= stroke.length' in tick_body
    assert 'complete = false' in tick_body
    assert 'requestAnimationFrame((nextTimestamp)' in tick_body
    assert 'strokeDashoffset' not in tick_body

    commit_start = routes_js.index('        commitMotionStroke(')
    commit_end = routes_js.index('\n        finishMotion()', commit_start)
    commit_body = routes_js[commit_start:commit_end]
    assert "stroke.path.style.visibility = 'visible'" in commit_body
    assert "stroke.path.style.strokeDasharray = 'none'" in commit_body
    assert "stroke.path.style.strokeDashoffset = '0'" in commit_body
    assert "stroke.path.style.removeProperty('stroke-linecap')" in commit_body

    assert 'adaAlarmFlow' not in routes_js
    assert 'animationend' not in routes_js
    assert 'animationstart' not in routes_js
    assert 'animationcancel' not in routes_js
    assert 'animation-delay' not in routes_js
    assert '.style.animation' not in routes_js
    assert 'new Promise' not in routes_js
    assert 'Promise.all' not in routes_js
    assert 'async playCard' not in routes_js

    assert routes_js.count('this.scheduleTimer(') == 1
    assert "'auto.next'" in routes_js
    assert "this.debug('auto.dwell'" in routes_js
    assert 'totalWait' not in routes_js
    assert "'phase.fan-out'" not in routes_js
    assert "'phase.impact'" not in routes_js

    assert 'INTERACTIVE_SELECTOR' in routes_js
    assert 'MutationObserver' in routes_js
    assert 'attributeFilter' not in routes_js
    assert "DEBUG_QUERY_PARAMETER = 'alarmTraceDebug'" in routes_js
    assert "this.debug('refresh.begin'" in routes_js
    assert "this.debug('visual.clear'" in routes_js
    assert "this.markGeometryDirty('resize')" in routes_js
    assert "this.ensureFreshCatalog('auto.present')" in routes_js
    assert 'this.observeGeometry([this.scope, this.root])' in routes_js
    assert 'schedulePresentationGeometrySync' in routes_js
    assert 'schedulePersistentGeometrySync' not in routes_js
    assert 'this.cancelMotion(reason);' in routes_js

    sync_start = routes_js.index('syncPresentationGeometry(eventId) {')
    sync_end = routes_js.index('buildCatalogSnapshot() {', sync_start)
    sync_body = routes_js[sync_start:sync_end]
    assert 'this.generation +=' not in sync_body
    assert '++this.generation' not in sync_body
    assert 'clearTimers' not in sync_body
    assert 'clearActiveVisualState' not in sync_body
    assert 'playCard' not in sync_body
    assert 'autoIndex =' not in sync_body
    assert 'pinnedEventId =' not in sync_body
    assert '.replaceWith(nextActiveSvg)' in sync_body
    assert '.replaceWith(nextImpactSvg)' in sync_body

    resize_start = routes_js.index('this.resizeObserver = new ResizeObserver')
    resize_end = routes_js.index('requestAnimationFrame(() => {', resize_start)
    resize_body = routes_js[resize_start:resize_end]
    assert "this.markGeometryDirty('resize')" in resize_body
    assert 'clearTimers' not in resize_body
    assert 'clearActiveVisualState' not in resize_body
    assert 'rebuildCatalog' not in resize_body

    assert 'setInterval' not in routes_js
    assert 'fetch(' not in routes_js
    assert js_list == ['10-dashboard-geometry.js', '20-dashboard-routes.js']


def test_alarm_js_manifest_declares_every_packaged_file_exactly_once() -> None:
    js_dir = (
        Path(__file__).parents[1]
        / 'src'
        / 'ada'
        / 'ui'
        / 'features'
        / 'alarms'
        / 'resources'
        / 'js'
    )
    declared = [
        line.strip() for line in (js_dir / 'js.list').read_text().splitlines() if line.strip()
    ]
    packaged = sorted(path.name for path in js_dir.glob('*.js'))

    assert sorted(declared) == packaged
    assert len(declared) == len(set(declared))
