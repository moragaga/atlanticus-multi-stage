from dash import html

from ada.ui.features.alarms.dashboard import (
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

_IO_COMPONENTS = (
    ('general_mine', 'General Mina'),
    ('loading', 'Carguío'),
    ('transport', 'Transporte'),
    ('crushing_stmg', 'Chancado-STMG'),
    ('stock_chacay', 'Stock Chacay'),
    ('grinding', 'Molienda'),
    ('flotation', 'Flotación'),
    ('fluid_transport', 'Transporte Fluidos'),
    ('port', 'Puerto'),
)
_PROCESS_ALARM_COUNT = 6
_PROCESS_ACTIVE_ALARM_INDEX = 2
_TRACE_DWELL_MS = 15_000
_PROCESS_ROTATION_INTERVAL_MS = 14_000
_PROCESS_DISTRIBUTED_INTERVAL_MS = 8_500


def build_reference_alarm_dashboard_baselines() -> html.Section:
    return html.Section(
        [
            html.H2('Alarm Dashboard Geometry'),
            html.P('Baseline permanente, placement y trazas de referencia sin motor de alarmas.'),
            html.Div(
                [
                    html.H3('Integrated Operations'),
                    html.Div(
                        [
                            _build_integrated_operations_same_point_reference(),
                            _build_integrated_operations_span_reference(),
                        ],
                        className='reference-ada__alarm-example-grid',
                    ),
                ],
                className='reference-ada__alarm-baseline-example',
            ),
            html.Div(
                [
                    html.H3('Process'),
                    html.Div(
                        [
                            _build_process_reference('full', ('left', 'center', 'right')),
                            _build_process_reference('left-center', ('left', 'center')),
                            _build_process_reference('center-right', ('center', 'right')),
                            _build_process_reference('center-only', ('center',)),
                        ],
                        className='reference-ada__alarm-process-variants',
                    ),
                ],
                className='reference-ada__alarm-baseline-example',
            ),
            html.Div(
                [
                    html.H3('Behavior Harness'),
                    html.P(
                        'Los tiempos están comprimidos para revisión visual. '
                        'Click en una card fija la traza; los botones internos no cambian el foco.'
                    ),
                    html.Div(
                        [
                            _build_integrated_operations_behavior_reference(),
                            _build_process_behavior_reference(),
                            _build_process_distributed_behavior_reference(),
                            _build_singleton_behavior_reference(),
                        ],
                        className='reference-ada__alarm-behavior-grid',
                    ),
                ],
                className='reference-ada__alarm-baseline-example',
            ),
        ],
        className='reference-ada__alarm-baselines',
    )


def _build_integrated_operations_same_point_reference() -> html.Div:
    target = _component_target_definition('general_mine')
    route = _route_definition(
        event_id='reference-io-same-point',
        assignment_key='component:general_mine',
        card_key='io_same_point_alarm',
        origin=target,
        impacts=(target,),
        tone=AlarmRouteTone.CRITICAL,
    )
    return _build_integrated_operations_static_scope(
        'Mismo punto · card alineada con General Mina',
        route,
        {'general_mine': ('io_same_point_alarm', 'Origen e impacto', AlarmRouteTone.CRITICAL)},
    )


def _build_integrated_operations_span_reference() -> html.Div:
    route = _route_definition(
        event_id='reference-io-span',
        assignment_key='component:loading',
        card_key='io_loading_alarm',
        origin=_component_target_definition('loading'),
        impacts=(
            _component_target_definition('flotation'),
            _component_target_definition('port'),
        ),
        tone=AlarmRouteTone.ATTENTION,
    )
    return _build_integrated_operations_static_scope(
        'Máximo visible de referencia · 3 Mina + 3 Planta',
        route,
        {
            'general_mine': ('io_general_mine_alarm', 'General Mina', AlarmRouteTone.CRITICAL),
            'loading': ('io_loading_alarm', 'Carguío', AlarmRouteTone.ATTENTION),
            'transport': ('io_transport_alarm', 'Transporte', AlarmRouteTone.CRITICAL),
            'crushing_stmg': ('io_crushing_alarm', 'Chancado-STMG', AlarmRouteTone.CRITICAL),
            'flotation': ('io_flotation_alarm', 'Flotación', AlarmRouteTone.ATTENTION),
            'port': ('io_port_alarm', 'Puerto', AlarmRouteTone.CRITICAL),
        },
    )


def _build_integrated_operations_static_scope(
    label: str,
    route: AlarmDashboardRouteDefinition,
    alarm_cards: dict[str, tuple[str, str, AlarmRouteTone]],
) -> html.Div:
    component_keys = tuple(key for key, _ in _IO_COMPONENTS)
    return html.Div(
        [
            html.Div(label, className='reference-ada__alarm-example-label'),
            html.Div(
                _build_integrated_operations_static_alarm_grid(alarm_cards, route),
                className='reference-ada__alarm-content-frame',
            ),
            build_alarm_dashboard_route_layer(route),
            build_integrated_operations_alarm_baseline(component_keys),
            html.Div(
                _build_integrated_operations_body_grid(),
                className='reference-ada__alarm-body-frame',
            ),
        ],
        className='reference-ada__alarm-geometry-scope',
        **alarm_geometry_scope_attributes(),
    )


def _build_integrated_operations_static_alarm_grid(
    alarm_cards: dict[str, tuple[str, str, AlarmRouteTone]],
    active_route: AlarmDashboardRouteDefinition,
) -> html.Div:
    return _build_integrated_operations_grid(
        lambda component_key: _static_io_alarm_slot(
            component_key,
            alarm_cards,
            active_route,
        )
    )


def _static_io_alarm_slot(
    component_key: str,
    alarm_cards: dict[str, tuple[str, str, AlarmRouteTone]],
    active_route: AlarmDashboardRouteDefinition,
) -> html.Div:
    alarm = alarm_cards.get(component_key)
    if alarm is None:
        return html.Div(className='reference-ada__alarm-card-slot')
    card_key, label, tone = alarm
    definition = active_route if card_key == active_route.card_key else None
    return html.Div(
        [_reference_alarm_card(card_key, label, tone, definition=definition)],
        className='reference-ada__alarm-card-slot',
    )


def _build_integrated_operations_behavior_reference() -> html.Div:
    lane_events = {
        'general_mine': (
            _route_definition(
                event_id='io-gm-001',
                assignment_key='component:general_mine',
                card_key='io_gm_001',
                origin=_component_target_definition('general_mine'),
                impacts=(_component_target_definition('general_mine'),),
                tone=AlarmRouteTone.CRITICAL,
            ),
            _route_definition(
                event_id='io-gm-002',
                assignment_key='component:general_mine',
                card_key='io_gm_002',
                origin=_component_target_definition('general_mine'),
                impacts=(_component_target_definition('general_mine'),),
                tone=AlarmRouteTone.ATTENTION,
            ),
        ),
        'loading': (
            _route_definition(
                event_id='io-load-001',
                assignment_key='component:loading',
                card_key='io_load_001',
                origin=_component_target_definition('loading'),
                impacts=(
                    _component_target_definition('flotation'),
                    _component_target_definition('port'),
                ),
                tone=AlarmRouteTone.ATTENTION,
            ),
        ),
        'transport': (
            _route_definition(
                event_id='io-transport-001',
                assignment_key='component:transport',
                card_key='io_transport_001',
                origin=_component_target_definition('transport'),
                impacts=(_component_target_definition('transport'),),
                tone=AlarmRouteTone.CRITICAL,
            ),
            _route_definition(
                event_id='io-transport-002',
                assignment_key='component:transport',
                card_key='io_transport_002',
                origin=_component_target_definition('transport'),
                impacts=(_component_target_definition('transport'),),
                tone=AlarmRouteTone.ATTENTION,
            ),
        ),
        'crushing_stmg': (
            _route_definition(
                event_id='io-crushing-001',
                assignment_key='component:crushing_stmg',
                card_key='io_crushing_001',
                origin=_component_target_definition('crushing_stmg'),
                impacts=(_component_target_definition('crushing_stmg'),),
                tone=AlarmRouteTone.CRITICAL,
            ),
        ),
        'flotation': (
            _route_definition(
                event_id='io-flotation-001',
                assignment_key='component:flotation',
                card_key='io_flotation_001',
                origin=_component_target_definition('flotation'),
                impacts=(_component_target_definition('flotation'),),
                tone=AlarmRouteTone.ATTENTION,
            ),
            _route_definition(
                event_id='io-flotation-002',
                assignment_key='component:flotation',
                card_key='io_flotation_002',
                origin=_component_target_definition('flotation'),
                impacts=(_component_target_definition('flotation'),),
                tone=AlarmRouteTone.CRITICAL,
            ),
        ),
        'port': (
            _route_definition(
                event_id='io-port-001',
                assignment_key='component:port',
                card_key='io_port_001',
                origin=_component_target_definition('port'),
                impacts=(_component_target_definition('port'),),
                tone=AlarmRouteTone.CRITICAL,
            ),
        ),
    }
    lane_intervals = {
        'general_mine': 9_000,
        'loading': 11_000,
        'transport': 12_500,
        'crushing_stmg': 10_000,
        'flotation': 14_000,
        'port': 13_000,
    }
    component_keys = tuple(key for key, _ in _IO_COMPONENTS)
    attributes = {
        **alarm_geometry_scope_attributes(),
        **alarm_presentation_scope_attributes(
            trace_dwell_ms=_TRACE_DWELL_MS,
            interaction=AlarmPresentationInteraction.INTERACTIVE,
        ),
        **alarm_visibility_scope_attributes(AlarmVisibilityStrategy.QUEUE_IN_QUEUE),
    }
    return html.Div(
        [
            html.Div(
                'IO · queue-in-queue · relojes independientes por posición',
                className='reference-ada__alarm-example-label',
            ),
            html.Div(
                _build_integrated_operations_grid(
                    lambda component_key: _behavior_io_alarm_slot(
                        component_key,
                        lane_events,
                        lane_intervals,
                    )
                ),
                className='reference-ada__alarm-content-frame',
            ),
            build_alarm_dashboard_route_layer(),
            build_integrated_operations_alarm_baseline(component_keys),
            html.Div(
                _build_integrated_operations_body_grid(),
                className='reference-ada__alarm-body-frame',
            ),
        ],
        className='reference-ada__alarm-geometry-scope',
        **attributes,
    )


def _behavior_io_alarm_slot(
    component_key: str,
    lane_events: dict[str, tuple[AlarmDashboardRouteDefinition, ...]],
    lane_intervals: dict[str, int],
) -> html.Div:
    definitions = lane_events.get(component_key, ())
    if not definitions:
        return html.Div(className='reference-ada__alarm-card-slot')
    return html.Div(
        [
            _reference_alarm_card(
                definition.card_key,
                definition.event_id,
                definition.tone,
                definition=definition,
                hidden=index > 0,
                include_button=True,
            )
            for index, definition in enumerate(definitions)
        ],
        className='reference-ada__alarm-card-slot reference-ada__alarm-queue-lane',
        **alarm_queue_lane_attributes(
            component_key,
            interval_ms=lane_intervals[component_key],
        ),
    )


def _build_integrated_operations_grid(slot_builder) -> html.Div:
    return html.Div(
        [
            slot_builder('general_mine'),
            html.Div(
                [slot_builder('loading'), slot_builder('transport')],
                className='reference-ada__alarm-io-double',
            ),
            *(
                slot_builder(key)
                for key in (
                    'crushing_stmg',
                    'stock_chacay',
                    'grinding',
                    'flotation',
                    'fluid_transport',
                    'port',
                )
            ),
        ],
        className='reference-ada__alarm-io-placement-grid',
    )


def _build_integrated_operations_body_grid() -> html.Div:
    by_key = dict(_IO_COMPONENTS)
    return html.Div(
        [
            _component_target('general_mine', by_key['general_mine']),
            html.Div(
                [
                    _component_target('loading', by_key['loading']),
                    _component_target('transport', by_key['transport']),
                ],
                className='reference-ada__alarm-io-double',
            ),
            *(
                _component_target(key, by_key[key])
                for key in (
                    'crushing_stmg',
                    'stock_chacay',
                    'grinding',
                    'flotation',
                    'fluid_transport',
                    'port',
                )
            ),
        ],
        className='reference-ada__alarm-io-grid',
    )


def _build_process_reference(variant: str, slots: tuple[str, ...]) -> html.Div:
    center = AlarmBaselineTarget(AlarmBaselineTargetKind.SLOT, 'center')
    prefix = f'process_{variant.replace("-", "_")}'
    route = _route_definition(
        event_id=f'reference-{prefix}',
        assignment_key=f'process_slot_{_PROCESS_ACTIVE_ALARM_INDEX + 1}',
        card_key=f'{prefix}_alarm_{_PROCESS_ACTIVE_ALARM_INDEX + 1}',
        origin=center,
        impacts=(center,),
        tone=AlarmRouteTone.CRITICAL,
    )
    labels = {
        'full': 'Left + Center + Right',
        'left-center': 'Left + Center',
        'center-right': 'Center + Right',
        'center-only': 'Center only',
    }
    return html.Div(
        [
            html.Div(labels[variant], className='reference-ada__alarm-example-label'),
            html.Div(
                _build_static_process_alarm_grid(prefix, route),
                className='reference-ada__alarm-content-frame',
            ),
            build_alarm_dashboard_route_layer(route),
            build_process_alarm_baseline(),
            html.Div(
                _build_process_body_grid(variant, slots),
                className='reference-ada__alarm-body-frame',
            ),
        ],
        className='reference-ada__alarm-geometry-scope',
        **alarm_geometry_scope_attributes(),
    )


def _build_static_process_alarm_grid(
    prefix: str,
    active_route: AlarmDashboardRouteDefinition,
) -> html.Div:
    cards = []
    for index in range(1, _PROCESS_ALARM_COUNT + 1):
        card_key = f'{prefix}_alarm_{index}'
        tone = AlarmRouteTone.CRITICAL if index % 2 else AlarmRouteTone.ATTENTION
        definition = active_route if card_key == active_route.card_key else None
        cards.append(
            _reference_alarm_card(
                card_key,
                f'Alarma {index}',
                tone,
                definition=definition,
            )
        )
    return html.Div(cards, className='reference-ada__alarm-process-placement-grid')


def _build_process_behavior_reference() -> html.Div:
    center = AlarmBaselineTarget(AlarmBaselineTargetKind.SLOT, 'center')
    definitions = tuple(
        _route_definition(
            event_id=f'process-normal-{index:03d}',
            assignment_key='process_pending',
            card_key=f'process_normal_{index:03d}',
            origin=center,
            impacts=(center,),
            tone=AlarmRouteTone.CRITICAL if index in {1, 4, 7} else AlarmRouteTone.ATTENTION,
        )
        for index in range(1, 9)
    )
    return _build_dynamic_process_scope(
        'Process · cola normal · 8 alarmas / 6 slots',
        definitions,
        distributed_definitions=(),
        rotation_interval_ms=_PROCESS_ROTATION_INTERVAL_MS,
        distributed_interval_ms=None,
    )


def _build_process_distributed_behavior_reference() -> html.Div:
    center = AlarmBaselineTarget(AlarmBaselineTargetKind.SLOT, 'center')
    normal = tuple(
        _route_definition(
            event_id=f'process-distributed-normal-{index:03d}',
            assignment_key='process_pending',
            card_key=f'process_distributed_normal_{index:03d}',
            origin=center,
            impacts=(center,),
            tone=AlarmRouteTone.CRITICAL if index % 3 == 0 else AlarmRouteTone.ATTENTION,
        )
        for index in range(1, 7)
    )
    distributed = tuple(
        _route_definition(
            event_id=f'process-distributed-special-{index:03d}',
            assignment_key='process_pending',
            card_key=f'process_distributed_special_{index:03d}',
            origin=center,
            impacts=(center,),
            tone=AlarmRouteTone.CRITICAL if index == 2 else AlarmRouteTone.ATTENTION,
        )
        for index in range(1, 4)
    )
    return _build_dynamic_process_scope(
        'Process distribuido · slot 6 reservado · dos relojes independientes',
        normal,
        distributed_definitions=distributed,
        rotation_interval_ms=_PROCESS_ROTATION_INTERVAL_MS,
        distributed_interval_ms=_PROCESS_DISTRIBUTED_INTERVAL_MS,
    )


def _build_dynamic_process_scope(
    label: str,
    normal_definitions: tuple[AlarmDashboardRouteDefinition, ...],
    *,
    distributed_definitions: tuple[AlarmDashboardRouteDefinition, ...],
    rotation_interval_ms: int,
    distributed_interval_ms: int | None,
) -> html.Div:
    definitions = normal_definitions + distributed_definitions
    attributes = {
        **alarm_geometry_scope_attributes(),
        **alarm_presentation_scope_attributes(
            trace_dwell_ms=_TRACE_DWELL_MS,
            interaction=AlarmPresentationInteraction.INTERACTIVE,
        ),
        **alarm_visibility_scope_attributes(
            AlarmVisibilityStrategy.PROCESS,
            rotation_interval_ms=rotation_interval_ms,
            distributed_interval_ms=distributed_interval_ms,
        ),
    }
    return html.Div(
        [
            html.Div(label, className='reference-ada__alarm-example-label'),
            html.Div(
                html.Div(
                    [
                        _reference_alarm_card(
                            definition.card_key,
                            definition.event_id,
                            definition.tone,
                            definition=definition,
                            distributed=definition in distributed_definitions,
                            hidden=True,
                            include_button=True,
                        )
                        for definition in definitions
                    ],
                    className='reference-ada__alarm-process-placement-grid',
                    **{'data-ada-alarm-process-queue': 'true'},
                ),
                className='reference-ada__alarm-content-frame',
            ),
            build_alarm_dashboard_route_layer(),
            build_process_alarm_baseline(),
            html.Div(
                _build_process_body_grid('full', ('left', 'center', 'right')),
                className='reference-ada__alarm-body-frame',
            ),
        ],
        className='reference-ada__alarm-geometry-scope',
        **attributes,
    )


def _build_singleton_behavior_reference() -> html.Div:
    center = AlarmBaselineTarget(AlarmBaselineTargetKind.SLOT, 'center')
    definition = _route_definition(
        event_id='process-singleton-001',
        assignment_key='process_slot_1',
        card_key='process_singleton_001',
        origin=center,
        impacts=(center,),
        tone=AlarmRouteTone.CRITICAL,
    )
    attributes = {
        **alarm_geometry_scope_attributes(),
        **alarm_presentation_scope_attributes(
            trace_dwell_ms=_TRACE_DWELL_MS,
            interaction=AlarmPresentationInteraction.INTERACTIVE,
        ),
    }
    return html.Div(
        [
            html.Div(
                'Singleton global · la traza permanece y el click no cambia el estado',
                className='reference-ada__alarm-example-label',
            ),
            html.Div(
                html.Div(
                    [
                        _reference_alarm_card(
                            definition.card_key,
                            'Única alarma activa',
                            definition.tone,
                            definition=definition,
                            include_button=True,
                        )
                    ],
                    className='reference-ada__alarm-process-placement-grid',
                ),
                className='reference-ada__alarm-content-frame',
            ),
            build_alarm_dashboard_route_layer(),
            build_process_alarm_baseline(),
            html.Div(
                _build_process_body_grid('center-only', ('center',)),
                className='reference-ada__alarm-body-frame',
            ),
        ],
        className='reference-ada__alarm-geometry-scope',
        **attributes,
    )


def _build_process_body_grid(variant: str, slots: tuple[str, ...]) -> html.Div:
    return html.Div(
        [_slot_target(slot, slot.title()) for slot in slots],
        className=(
            f'reference-ada__alarm-process-grid reference-ada__alarm-process-grid--{variant}'
        ),
    )


def _reference_alarm_card(
    card_key: str,
    label: str,
    tone: AlarmRouteTone,
    *,
    definition: AlarmDashboardRouteDefinition | None = None,
    distributed: bool = False,
    hidden: bool = False,
    include_button: bool = False,
) -> html.Div:
    attributes: dict[str, str | bool] = {
        **alarm_card_identity_attributes(card_key),
        'data-ada-alarm-card-tone': tone.value,
        'hidden': hidden,
    }
    if definition is not None:
        attributes.update(
            alarm_card_presentation_attributes(
                definition,
                distributed=distributed,
            )
        )
    children = [
        html.Div(
            'CRITICAL' if tone is AlarmRouteTone.CRITICAL else 'ATTENTION',
            className='reference-ada__alarm-card-band',
        ),
        html.Div(label, className='reference-ada__alarm-card-body'),
    ]
    if include_button:
        children.append(
            html.Div(
                html.Button('Info', type='button', className='reference-ada__alarm-card-action'),
                className='reference-ada__alarm-card-footer',
            )
        )
    return html.Div(
        children,
        className='reference-ada__alarm-card',
        **attributes,
    )


def _route_definition(
    *,
    event_id: str,
    assignment_key: str,
    card_key: str,
    origin: AlarmBaselineTarget,
    impacts: tuple[AlarmBaselineTarget, ...],
    tone: AlarmRouteTone,
) -> AlarmDashboardRouteDefinition:
    return AlarmDashboardRouteDefinition(
        event_id=event_id,
        assignment_key=assignment_key,
        card_key=card_key,
        origin=origin,
        impacts=impacts,
        tone=tone,
    )


def _component_target_definition(key: str) -> AlarmBaselineTarget:
    return AlarmBaselineTarget(AlarmBaselineTargetKind.COMPONENT, key)


def _component_target(key: str, label: str) -> html.Div:
    return html.Div(
        label,
        className='reference-ada__alarm-target',
        **{
            **component_identity_attributes(key),
            'data-ada-alarm-impact': 'none',
        },
    )


def _slot_target(key: str, label: str) -> html.Div:
    return html.Div(
        label,
        className=f'reference-ada__alarm-target reference-ada__alarm-target--{key}',
        **{
            **slot_identity_attributes(key),
            'data-ada-alarm-impact': 'none',
        },
    )
