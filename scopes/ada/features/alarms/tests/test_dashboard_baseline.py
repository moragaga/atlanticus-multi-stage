from pathlib import Path

import pytest

from ada.features.alarms import AlarmDefinitionError
from ada.features.alarms.dashboard import (
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
from ada.ui.framework.core import (
    component_identity_attributes,
    slot_identity_attributes,
    subcomponent_identity_attributes,
)


def _props(component) -> dict[str, object]:
    return component.to_plotly_json()['props']


def _route_definition(
    *,
    event_id: str = 'event-001',
    assignment_key: str = 'component:loading',
    placement_key: str = 'io-loading-slot-1',
    card_key: str = 'alarm_1',
    tone: AlarmRouteTone = AlarmRouteTone.CRITICAL,
) -> AlarmDashboardRouteDefinition:
    origin = AlarmBaselineTarget(AlarmBaselineTargetKind.COMPONENT, 'loading')
    affected = AlarmBaselineTarget(
        AlarmBaselineTargetKind.SUBCOMPONENT,
        'loading_subcomponent_1',
    )
    return AlarmDashboardRouteDefinition(
        event_id=event_id,
        assignment_key=assignment_key,
        placement_key=placement_key,
        card_key=card_key,
        origin=origin,
        destinations=(origin,),
        affected_targets=(affected,),
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


def test_dom_contract_exposes_stable_scope_target_and_alarm_card_attributes() -> None:
    assert alarm_geometry_scope_attributes() == {'data-ada-alarm-geometry-scope': 'true'}
    assert component_identity_attributes('grinding') == {'data-ada-component-key': 'grinding'}
    assert subcomponent_identity_attributes('flotation_selective') == {
        'data-ada-subcomponent-key': 'flotation_selective'
    }
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
        placement_key='io-loading-slot-2',
        card_key='alarm_2',
        origin=origin,
        destinations=(
            AlarmBaselineTarget(AlarmBaselineTargetKind.COMPONENT, 'flotation'),
            AlarmBaselineTarget(AlarmBaselineTargetKind.COMPONENT, 'port'),
        ),
        affected_targets=(
            AlarmBaselineTarget(AlarmBaselineTargetKind.SUBCOMPONENT, 'flotation_selective'),
            AlarmBaselineTarget(AlarmBaselineTargetKind.SUBCOMPONENT, 'port_shipping'),
        ),
        tone=AlarmRouteTone.ATTENTION,
    )

    assert span.event_id == 'event-abc-123'
    assert span.assignment_key == 'component:loading'
    assert span.placement_key == 'io-loading-slot-2'
    assert tuple(target.key for target in span.destinations) == ('flotation', 'port')
    assert tuple(target.kind for target in span.affected_targets) == (
        AlarmBaselineTargetKind.SUBCOMPONENT,
        AlarmBaselineTargetKind.SUBCOMPONENT,
    )
    assert tuple(target.key for target in span.affected_targets) == (
        'flotation_selective',
        'port_shipping',
    )


def test_process_route_targets_only_the_complete_center_card() -> None:
    center = AlarmBaselineTarget(AlarmBaselineTargetKind.SLOT, 'center')

    definition = AlarmDashboardRouteDefinition(
        event_id='process-001',
        assignment_key='process_slot_1',
        placement_key='process-slot-1',
        card_key='process_alarm_1',
        origin=center,
        destinations=(center,),
        affected_targets=(center,),
        tone=AlarmRouteTone.CRITICAL,
    )

    attributes = alarm_card_presentation_attributes(definition)

    assert attributes['data-ada-alarm-route-origin'] == 'slot:center'
    assert attributes['data-ada-alarm-route-destinations'] == 'slot:center'
    assert attributes['data-ada-alarm-affected-targets'] == 'slot:center'


def test_route_definition_rejects_empty_or_duplicate_target_groups() -> None:
    origin = AlarmBaselineTarget(AlarmBaselineTargetKind.SLOT, 'center')

    with pytest.raises(AlarmDefinitionError, match='Invalid alarm placement key'):
        AlarmDashboardRouteDefinition(
            event_id='event-001',
            assignment_key='process_slot_1',
            placement_key=' ',
            card_key='alarm_1',
            origin=origin,
            destinations=(origin,),
            affected_targets=(origin,),
            tone=AlarmRouteTone.CRITICAL,
        )

    with pytest.raises(AlarmDefinitionError, match='at least one route destination'):
        AlarmDashboardRouteDefinition(
            event_id='event-001',
            assignment_key='process_slot_1',
            placement_key='process-slot-1',
            card_key='alarm_1',
            origin=origin,
            destinations=(),
            affected_targets=(origin,),
            tone=AlarmRouteTone.CRITICAL,
        )

    with pytest.raises(AlarmDefinitionError, match='duplicate affected targets'):
        AlarmDashboardRouteDefinition(
            event_id='event-001',
            assignment_key='process_slot_1',
            placement_key='process-slot-1',
            card_key='alarm_1',
            origin=origin,
            destinations=(origin,),
            affected_targets=(origin, origin),
            tone=AlarmRouteTone.CRITICAL,
        )


def test_card_presentation_serializes_event_assignment_tone_and_route_geometry() -> None:
    definition = _route_definition(tone=AlarmRouteTone.ATTENTION)

    attributes = alarm_card_presentation_attributes(definition, distributed=True)

    assert attributes['data-ada-alarm-card-key'] == 'alarm_1'
    assert attributes['data-ada-alarm-event-id'] == 'event-001'
    assert attributes['data-ada-alarm-assignment-key'] == 'component:loading'
    assert attributes['data-ada-alarm-placement-key'] == 'io-loading-slot-1'
    assert attributes['data-ada-alarm-card-tone'] == 'attention'
    assert attributes['data-ada-alarm-route-origin'] == 'component:loading'
    assert attributes['data-ada-alarm-route-destinations'] == 'component:loading'
    assert attributes['data-ada-alarm-affected-targets'] == ('subcomponent:loading_subcomponent_1')
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
    assert seeded['data-ada-alarm-route-placement-key'] == 'io-loading-slot-1'
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
        Path(__file__).parents[1] / 'src' / 'ada' / 'features' / 'alarms' / 'ui' / 'resources'
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
    assert 'MOTION_SAMPLE_STEP_PX = 2' in routes_js
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
    assert 'destinationSegments,' in routes_js
    assert 'destinationRouteSegments(' in routes_js
    assert 'let cursorX = originX;' in routes_js
    assert 'cursorX = x;' in routes_js
    assert 'destinationLegs' not in routes_js
    assert 'contextSegments: [' in routes_js
    assert 'createImpactPaths' in routes_js
    assert 'createImpactPath(' not in routes_js
    assert 'return [leftPath, rightPath];' in routes_js

    assert 'startMotion(' in routes_js
    assert 'createMotionSteps(' in routes_js
    assert 'beginNextMotionStep()' in routes_js
    assert 'tickMotion(timestamp)' in routes_js
    assert 'prepareMotionStroke(' in routes_js
    assert 'createMotionSamples(' in routes_js
    assert 'motionPrefixData(' in routes_js
    assert 'commitMotionStroke(' in routes_js
    assert 'finishMotion()' in routes_js
    assert 'cancelMotion(reason)' in routes_js
    assert "stage: 'shared-trunk'" in routes_js
    assert '`destination-leg:${target.kind}:${target.key}`' in routes_js
    assert '`affected:${target.kind}:${target.key}`' in routes_js
    assert "const side = pathIndex === 0 ? 'left' : 'right';" in routes_js
    assert 'this.motion.stepDurationMs = this.motionStepDuration(' in routes_js
    assert 'lastTimestamp: null' in routes_js
    assert 'stepElapsedMs: 0' in routes_js
    assert 'stepStartedAt' not in routes_js

    speed_start = routes_js.index('        motionSpeed() {')
    speed_end = routes_js.index('\n        startMotion(', speed_start)
    speed_body = routes_js[speed_start:speed_end]
    assert 'getBoundingClientRect().width' in speed_body
    assert 'width * MOTION_SCOPE_WIDTHS_PER_SECOND' in speed_body
    assert 'MAX_MOTION_SPEED_PX_PER_SECOND' in speed_body
    assert 'MIN_MOTION_SPEED_PX_PER_SECOND' in speed_body

    stroke_start = routes_js.index('        prepareMotionStroke(')
    stroke_end = routes_js.index('\n        createMotionSamples(', stroke_start)
    stroke_body = routes_js[stroke_start:stroke_end]
    assert "path.style.visibility = 'hidden'" in stroke_body
    assert "path.style.opacity = '0'" in stroke_body
    assert "path.style.strokeLinecap = 'butt'" in stroke_body
    assert 'container.appendChild(path)' in stroke_body
    assert 'path.getTotalLength()' in stroke_body
    assert "const fullData = path.getAttribute('d') || '';" in stroke_body
    assert 'samples = this.createMotionSamples(path, length);' in stroke_body
    assert "path.setAttribute('d', this.motionPrefixData(stroke, 0));" in stroke_body
    assert 'strokeDash' not in stroke_body

    samples_start = routes_js.index('        createMotionSamples(')
    samples_end = routes_js.index('\n        motionPrefixData(', samples_start)
    samples_body = routes_js[samples_start:samples_end]
    assert 'Math.ceil(length / MOTION_SAMPLE_STEP_PX)' in samples_body
    assert 'path.getPointAtLength(distance)' in samples_body

    prefix_start = routes_js.index('        motionPrefixData(')
    prefix_end = routes_js.index('\n        motionPointCommand(', prefix_start)
    prefix_body = routes_js[prefix_start:prefix_end]
    assert "const commands = [this.motionPointCommand('M', stroke.samples[0])];" in prefix_body
    assert "commands.push(this.motionPointCommand('L', stroke.samples[index]));" in prefix_body
    assert "return commands.join(' ');" in prefix_body

    impact_duration_start = routes_js.index('        motionStepDuration(')
    impact_duration_end = routes_js.index('\n        easeAffectedProgress(', impact_duration_start)
    impact_duration_body = routes_js[impact_duration_start:impact_duration_end]
    assert 'Math.max(...strokes.map((stroke) => stroke.length))' in impact_duration_body
    assert '(longest / this.motion.speed) * 1000' in impact_duration_body
    assert "if (type === 'route')" in impact_duration_body
    assert 'IMPACT_MIN_DURATION_MS' in impact_duration_body
    assert 'IMPACT_MAX_DURATION_MS' in impact_duration_body

    reveal_start = routes_js.index('        revealMotionStroke(')
    reveal_end = routes_js.index('\n        completeMotionStep(', reveal_start)
    reveal_body = routes_js[reveal_start:reveal_end]
    assert (
        "stroke.path.setAttribute('d', this.motionPrefixData(stroke, visibleLength));"
        in reveal_body
    )
    assert 'strokeDash' not in reveal_body

    tick_start = routes_js.index('        tickMotion(timestamp) {')
    tick_end = routes_js.index('\n        commitMotionStroke(', tick_start)
    tick_body = routes_js[tick_start:tick_end]
    assert 'timestamp - this.motion.lastTimestamp' in tick_body
    assert 'let remainingMs =' in tick_body
    assert 'while (this.motion?.step' in tick_body
    assert 'const consumedMs = Math.min(remainingMs, availableMs);' in tick_body
    assert 'motion.stepElapsedMs += consumedMs;' in tick_body
    assert 'remainingMs -= consumedMs;' in tick_body
    assert "motion.step.type === 'affected'" in tick_body
    assert 'this.easeAffectedProgress(rawProgress)' in tick_body
    assert 'const visibleLength = stroke.length * progress;' in tick_body
    assert 'this.revealMotionStroke(stroke, visibleLength)' in tick_body
    assert 'rawProgress >= 1' in tick_body
    assert 'requestAnimationFrame((nextTimestamp)' in tick_body
    assert 'strokeDash' not in tick_body

    commit_start = routes_js.index('        commitMotionStroke(')
    commit_end = routes_js.index('\n        finishMotion()', commit_start)
    commit_body = routes_js[commit_start:commit_end]
    assert "stroke.path.setAttribute('d', stroke.fullData)" in commit_body
    assert "stroke.path.style.visibility = 'visible'" in commit_body
    assert "stroke.path.style.removeProperty('stroke-linecap')" in commit_body
    assert 'strokeDash' not in commit_body

    assert 'strokeDasharray' not in routes_js
    assert 'strokeDashoffset' not in routes_js
    assert 'pathLength' not in routes_js

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
    assert 'this.reconcilePresentation(' in routes_js
    assert 'previousSpecification.placementKey !== nextSpecification.placementKey' in routes_js
    assert 'previousSpecification.signature !== nextSpecification.signature' in routes_js
    assert 'this.pendingPresentationReconcile = true;' in routes_js
    assert 'this.restartAutoAt(replayIndex' in routes_js
    assert 'card.dataset.adaAlarmPlacementKey' in routes_js
    assert 'this.root.dataset.adaAlarmRoutePlacementKey = specification.placementKey;' in routes_js
    assert "this.ensureFreshCatalog('auto.present')" in routes_js
    assert 'this.observeGeometry([this.scope, this.root])' in routes_js
    assert 'schedulePresentationGeometrySync' in routes_js
    assert 'schedulePersistentGeometrySync' not in routes_js
    assert 'this.cancelMotion(reason);' in routes_js

    sync_start = routes_js.index('syncPresentationGeometry(eventId) {')
    sync_end = routes_js.index('reconcilePresentation(reason) {', sync_start)
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

    target_start = routes_js.index('        findTarget(target) {')
    target_end = routes_js.index('\n        findNode(target) {', target_start)
    target_body = routes_js[target_start:target_end]
    assert "component: 'data-ada-component-key'" in target_body
    assert "subcomponent: 'data-ada-subcomponent-key'" in target_body
    assert "slot: 'data-ada-slot-key'" in target_body
    assert 'if (!attribute)' in target_body

    affected_start = routes_js.index('        resolveAffectedTargets(targets) {')
    affected_end = routes_js.index('\n        cardSpecificationSignature(card) {', affected_start)
    affected_body = routes_js[affected_start:affected_end]
    assert "if (target.kind === 'component')" in affected_body
    assert "component.querySelectorAll('[data-ada-subcomponent-key]')" in affected_body
    assert "kind: 'subcomponent'" in affected_body
    assert 'const identities = new Set();' in affected_body
    assert 'resolved.push(entry);' in affected_body

    assert 'setInterval' not in routes_js
    assert 'fetch(' not in routes_js
    assert js_list == ['10-dashboard-geometry.js', '20-dashboard-routes.js']


def test_alarm_js_manifest_declares_every_packaged_file_exactly_once() -> None:
    js_dir = (
        Path(__file__).parents[1]
        / 'src'
        / 'ada'
        / 'features'
        / 'alarms'
        / 'ui'
        / 'resources'
        / 'js'
    )
    declared = [
        line.strip() for line in (js_dir / 'js.list').read_text().splitlines() if line.strip()
    ]
    packaged = sorted(path.name for path in js_dir.glob('*.js'))

    assert sorted(declared) == packaged
    assert len(declared) == len(set(declared))


def test_integrated_operations_baseline_can_project_scopes_without_changing_targets() -> None:
    baseline = build_integrated_operations_alarm_baseline(
        ('general_mina', 'flotacion'),
        component_scopes={
            'general_mina': 'mine',
            'flotacion': 'plant',
        },
    )
    props = _props(baseline)
    divider = props['children'][1]
    nodes = props['children'][2:]

    assert props['data-ada-alarm-scoped'] == 'true'
    assert 'ada-alarm-dashboard-baseline--scoped' in props['className']
    assert _props(divider)['className'] == 'ada-alarm-dashboard-baseline__scope-divider'
    assert tuple(_props(node)['data-ada-alarm-target-key'] for node in nodes) == (
        'general_mina',
        'flotacion',
    )
    assert tuple(_props(node)['data-ada-alarm-scope'] for node in nodes) == ('mine', 'plant')
    assert tuple(_props(node)['data-scope'] for node in nodes) == ('mine', 'plant')


def test_scoped_baseline_rejects_incomplete_scope_mapping() -> None:
    with pytest.raises(AlarmDefinitionError, match='scope mapping must match baseline targets'):
        build_integrated_operations_alarm_baseline(
            ('general_mina', 'flotacion'),
            component_scopes={'general_mina': 'mine'},
        )


def test_process_baseline_remains_unscoped_and_keeps_original_structure() -> None:
    process = build_process_alarm_baseline()
    props = _props(process)

    assert 'data-ada-alarm-scoped' not in props
    assert len(props['children']) == 2
    assert _props(props['children'][0])['className'] == 'ada-alarm-dashboard-baseline__line'
    assert _props(props['children'][1])['data-ada-alarm-target-key'] == 'center'
    assert 'data-ada-alarm-scope' not in _props(props['children'][1])


def test_alarm_route_player_exposes_geometry_only_refresh_event() -> None:
    from importlib.resources import files

    routes = (
        files('ada.features.alarms')
        .joinpath('ui', 'resources', 'js', '20-dashboard-routes.js')
        .read_text()
    )

    assert "const GEOMETRY_REFRESH_EVENT = 'ada:alarm-geometry-refresh';" in routes
    assert "this.onGeometryRefresh = () => this.markGeometryDirty('external');" in routes


def test_alarm_baseline_geometry_hides_offscreen_nodes_instead_of_clamping_to_viewport_edges() -> None:
    from importlib.resources import files

    geometry = (
        files('ada.features.alarms')
        .joinpath('ui', 'resources', 'js', '10-dashboard-geometry.js')
        .read_text()
    )

    assert 'if (rawX < halfNode || rawX > rootRect.width - halfNode)' in geometry
    assert "node.dataset.adaAlarmPositioned = 'false';" in geometry
    assert 'node.style.left = `${rawX}px`;' in geometry
    assert 'Math.min(\n                    Math.max(rawX, halfNode)' not in geometry
