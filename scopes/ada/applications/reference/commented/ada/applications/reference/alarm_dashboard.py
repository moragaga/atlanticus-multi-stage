from dash import html

from ada.ui.features.alarms.dashboard import (
    AlarmBaselineTarget,
    AlarmBaselineTargetKind,
    AlarmDashboardRouteDefinition,
    AlarmPresentationInteraction,
    AlarmRouteTone,
    alarm_card_identity_attributes,
    alarm_card_presentation_attributes,
    alarm_geometry_scope_attributes,
    alarm_presentation_scope_attributes,
    build_alarm_dashboard_route_layer,
    build_integrated_operations_alarm_baseline,
    build_process_alarm_baseline,
)
from ada.ui.framework.core import (
    component_identity_attributes,
    slot_identity_attributes,
    subcomponent_identity_attributes,
)

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
# Fixture variable 1..N: en producción estos hijos provienen del Tool Manifest.
_IO_SUBCOMPONENTS = {
    'general_mine': (('general_mine_subcomponent_1', 'Subcomponente 1'),),
    'loading': (
        ('loading_subcomponent_1', 'Subcomponente 1'),
        ('loading_subcomponent_2', 'Subcomponente 2'),
    ),
    'transport': (
        ('transport_subcomponent_1', 'Subcomponente 1'),
        ('transport_subcomponent_2', 'Subcomponente 2'),
        ('transport_subcomponent_3', 'Subcomponente 3'),
    ),
    'crushing_stmg': (
        ('crushing_stmg_subcomponent_1', 'Subcomponente 1'),
        ('crushing_stmg_subcomponent_2', 'Subcomponente 2'),
    ),
    'stock_chacay': (('stock_chacay_subcomponent_1', 'Subcomponente 1'),),
    'grinding': (
        ('grinding_subcomponent_1', 'Subcomponente 1'),
        ('grinding_subcomponent_2', 'Subcomponente 2'),
        ('grinding_subcomponent_3', 'Subcomponente 3'),
    ),
    'flotation': (
        ('flotation_selective', 'Selectiva'),
        ('flotation_collective', 'Colectiva'),
    ),
    'fluid_transport': (
        ('fluid_transport_subcomponent_1', 'Subcomponente 1'),
        ('fluid_transport_subcomponent_2', 'Subcomponente 2'),
        ('fluid_transport_subcomponent_3', 'Subcomponente 3'),
    ),
    'port': (
        ('port_subcomponent_1', 'Subcomponente 1'),
        ('port_subcomponent_2', 'Subcomponente 2'),
    ),
}
_PROCESS_ALARM_COUNT = 6
_PROCESS_ACTIVE_ALARM_INDEX = 2
# Tiempo de observación posterior a completar ruta e impactos.
_TRACE_DWELL_MS = 15_000


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
                    html.H3('Trace Player Reset'),
                    html.P(
                        'Sin scheduler de visibilidad: todas las rutas permanecen blancas, '
                        'la ruta activa avanza en rojo/amarillo, los impactos del body se '
                        'marcan progresivamente y el estado completo permanece 15 segundos.'
                    ),
                    html.Div(
                        [
                            _build_integrated_operations_player_reference(),
                            _build_process_player_reference(),
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
        placement_key='io-static-general-mine',
        card_key='io_same_point_alarm',
        origin=target,
        destinations=(target,),
        affected_targets=(_subcomponent_target_definition('general_mine_subcomponent_1'),),
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
        placement_key='io-static-loading',
        card_key='io_loading_alarm',
        origin=_component_target_definition('loading'),
        destinations=(
            _component_target_definition('flotation'),
            _component_target_definition('port'),
        ),
        affected_targets=(
            _component_target_definition('flotation'),
            _subcomponent_target_definition('port_subcomponent_1'),
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
        lambda component_key: _static_io_alarm_slot(component_key, alarm_cards, active_route)
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


# Harness IO sin scheduler: permite validar rutas con uno o varios impactos de body.
def _build_integrated_operations_player_reference() -> html.Div:
    definitions = {
        'general_mine': _route_definition(
            event_id='io-player-gm-001',
            assignment_key='component:general_mine',
            placement_key='io-general-mine-slot-1',
            card_key='io_player_gm_001',
            origin=_component_target_definition('general_mine'),
            destinations=(_component_target_definition('general_mine'),),
            affected_targets=(_subcomponent_target_definition('general_mine_subcomponent_1'),),
            tone=AlarmRouteTone.CRITICAL,
        ),
        'loading': _route_definition(
            event_id='io-player-load-001',
            assignment_key='component:loading',
            placement_key='io-loading-slot-1',
            card_key='io_player_load_001',
            origin=_component_target_definition('loading'),
            destinations=(
                _component_target_definition('flotation'),
                _component_target_definition('fluid_transport'),
                _component_target_definition('port'),
            ),
            affected_targets=(
                _subcomponent_target_definition('flotation_selective'),
                _subcomponent_target_definition('fluid_transport_subcomponent_2'),
                _subcomponent_target_definition('port_subcomponent_2'),
            ),
            tone=AlarmRouteTone.ATTENTION,
        ),
        'transport': _route_definition(
            event_id='io-player-transport-001',
            assignment_key='component:transport',
            placement_key='io-transport-slot-1',
            card_key='io_player_transport_001',
            origin=_component_target_definition('transport'),
            destinations=(_component_target_definition('transport'),),
            affected_targets=(_subcomponent_target_definition('transport_subcomponent_2'),),
            tone=AlarmRouteTone.CRITICAL,
        ),
        'crushing_stmg': _route_definition(
            event_id='io-player-crushing-001',
            assignment_key='component:crushing_stmg',
            placement_key='io-crushing-stmg-slot-1',
            card_key='io_player_crushing_001',
            origin=_component_target_definition('crushing_stmg'),
            destinations=(_component_target_definition('crushing_stmg'),),
            affected_targets=(_subcomponent_target_definition('crushing_stmg_subcomponent_1'),),
            tone=AlarmRouteTone.CRITICAL,
        ),
        'flotation': _route_definition(
            event_id='io-player-flotation-001',
            assignment_key='component:flotation',
            placement_key='io-flotation-slot-1',
            card_key='io_player_flotation_001',
            origin=_component_target_definition('flotation'),
            destinations=(
                _component_target_definition('grinding'),
                _component_target_definition('flotation'),
            ),
            affected_targets=(
                _subcomponent_target_definition('grinding_subcomponent_2'),
                _component_target_definition('flotation'),
            ),
            tone=AlarmRouteTone.ATTENTION,
        ),
        'port': _route_definition(
            event_id='io-player-port-001',
            assignment_key='component:port',
            placement_key='io-port-slot-1',
            card_key='io_player_port_001',
            origin=_component_target_definition('port'),
            destinations=(_component_target_definition('port'),),
            affected_targets=(_subcomponent_target_definition('port_subcomponent_1'),),
            tone=AlarmRouteTone.CRITICAL,
        ),
    }
    component_keys = tuple(key for key, _ in _IO_COMPONENTS)
    return html.Div(
        [
            html.Div(
                'IO · player aislado · incluye impactos de 1, 2 y 3 cards del body',
                className='reference-ada__alarm-example-label',
            ),
            html.Div(
                _build_integrated_operations_grid(
                    lambda component_key: _player_io_alarm_slot(
                        component_key,
                        definitions,
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
        **{
            **alarm_geometry_scope_attributes(),
            **alarm_presentation_scope_attributes(
                trace_dwell_ms=_TRACE_DWELL_MS,
                interaction=AlarmPresentationInteraction.INTERACTIVE,
            ),
        },
    )


def _player_io_alarm_slot(
    component_key: str,
    definitions: dict[str, AlarmDashboardRouteDefinition],
) -> html.Div:
    definition = definitions.get(component_key)
    if definition is None:
        return html.Div(className='reference-ada__alarm-card-slot')
    return html.Div(
        [
            _reference_alarm_card(
                definition.card_key,
                definition.event_id,
                definition.tone,
                definition=definition,
                include_button=True,
            )
        ],
        className='reference-ada__alarm-card-slot',
    )


def _build_process_reference(variant: str, slots: tuple[str, ...]) -> html.Div:
    center = AlarmBaselineTarget(AlarmBaselineTargetKind.SLOT, 'center')
    prefix = f'process_{variant.replace("-", "_")}'
    route = _route_definition(
        event_id=f'reference-{prefix}',
        assignment_key=f'process_slot_{_PROCESS_ACTIVE_ALARM_INDEX + 1}',
        placement_key=f'{prefix}-slot-{_PROCESS_ACTIVE_ALARM_INDEX + 1}',
        card_key=f'{prefix}_alarm_{_PROCESS_ACTIVE_ALARM_INDEX + 1}',
        origin=center,
        destinations=(center,),
        affected_targets=(center,),
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


# Harness Process sin rotación de cards: seis slots fijos para aislar el trace player.
def _build_process_player_reference() -> html.Div:
    center = AlarmBaselineTarget(AlarmBaselineTargetKind.SLOT, 'center')
    definitions = tuple(
        _route_definition(
            event_id=f'process-player-{index:03d}',
            assignment_key=f'process_slot_{index}',
            placement_key=f'process-slot-{index}',
            card_key=f'process_player_{index:03d}',
            origin=center,
            destinations=(center,),
            affected_targets=(center,),
            tone=AlarmRouteTone.CRITICAL if index in {1, 4} else AlarmRouteTone.ATTENTION,
        )
        for index in range(1, _PROCESS_ALARM_COUNT + 1)
    )
    return html.Div(
        [
            html.Div(
                'Process · center fijo · una única card del body afectada',
                className='reference-ada__alarm-example-label',
            ),
            html.Div(
                html.Div(
                    [
                        _reference_alarm_card(
                            definition.card_key,
                            definition.event_id,
                            definition.tone,
                            definition=definition,
                            include_button=True,
                        )
                        for definition in definitions
                    ],
                    className='reference-ada__alarm-process-placement-grid',
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
        **{
            **alarm_geometry_scope_attributes(),
            **alarm_presentation_scope_attributes(
                trace_dwell_ms=_TRACE_DWELL_MS,
                interaction=AlarmPresentationInteraction.INTERACTIVE,
            ),
        },
    )


def _build_integrated_operations_grid(slot_builder) -> html.Div:
    return html.Div(
        [slot_builder(key) for key, _ in _IO_COMPONENTS],
        className='reference-ada__alarm-io-placement-grid',
    )


def _build_integrated_operations_body_grid() -> html.Div:
    return html.Div(
        [_component_lane(key, label) for key, label in _IO_COMPONENTS],
        className='reference-ada__alarm-io-grid',
    )


def _build_process_body_grid(variant: str, slots: tuple[str, ...]) -> html.Div:
    return html.Div(
        [_slot_target(slot, slot.title()) for slot in slots],
        className=(
            f'reference-ada__alarm-process-grid reference-ada__alarm-process-grid--{variant}'
        ),
    )


# La alarm card conserva siempre su rojo/amarillo; el player no altera su borde ni fondo.
def _reference_alarm_card(
    card_key: str,
    label: str,
    tone: AlarmRouteTone,
    *,
    definition: AlarmDashboardRouteDefinition | None = None,
    include_button: bool = False,
) -> html.Div:
    attributes: dict[str, str] = {
        **alarm_card_identity_attributes(card_key),
        'data-ada-alarm-card-tone': tone.value,
    }
    if definition is not None:
        attributes.update(alarm_card_presentation_attributes(definition))
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
    placement_key: str,
    card_key: str,
    origin: AlarmBaselineTarget,
    destinations: tuple[AlarmBaselineTarget, ...],
    affected_targets: tuple[AlarmBaselineTarget, ...],
    tone: AlarmRouteTone,
) -> AlarmDashboardRouteDefinition:
    return AlarmDashboardRouteDefinition(
        event_id=event_id,
        assignment_key=assignment_key,
        placement_key=placement_key,
        card_key=card_key,
        origin=origin,
        destinations=destinations,
        affected_targets=affected_targets,
        tone=tone,
    )


def _component_target_definition(key: str) -> AlarmBaselineTarget:
    return AlarmBaselineTarget(AlarmBaselineTargetKind.COMPONENT, key)


# El contorno apunta a una card concreta y nunca al lane del componente.
def _subcomponent_target_definition(key: str) -> AlarmBaselineTarget:
    return AlarmBaselineTarget(AlarmBaselineTargetKind.SUBCOMPONENT, key)


# El lane da posición al punto; las cards son hijas directas y visualmente independientes.
def _component_lane(key: str, label: str) -> html.Div:
    return html.Div(
        [
            html.Div(label, className='reference-ada__alarm-component-label'),
            *(
                html.Div(
                    subcomponent_label,
                    className='reference-ada__alarm-subcomponent-card',
                    **subcomponent_identity_attributes(subcomponent_key),
                )
                for subcomponent_key, subcomponent_label in _IO_SUBCOMPONENTS[key]
            ),
        ],
        className='reference-ada__alarm-component-lane',
        **component_identity_attributes(key),
    )


def _slot_target(key: str, label: str) -> html.Div:
    return html.Div(
        label,
        className=f'reference-ada__alarm-target reference-ada__alarm-target--{key}',
        **slot_identity_attributes(key),
    )
