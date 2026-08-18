# Espejo comentado: harness de alarmas de referencia y helper reutilizable de card.
from dash import html

from ada.features.alarms.dashboard import (
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
_TRACE_DWELL_MS = 15_000


def build_reference_alarm_interaction() -> html.Section:
    return html.Section(
        [
            html.H2('Alarm Interaction'),
            html.P(
                'Players interactivos certificados para IO y Process; las muestras estáticas '
                'anteriores fueron retiradas para no duplicar geometrías de referencia.'
            ),
            html.Div(
                [
                    _build_integrated_operations_player_reference(),
                    _build_process_player_reference(),
                ],
                className='reference-ada__alarm-behavior-grid',
            ),
        ],
        className='reference-ada__alarm-baselines',
    )


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
            build_reference_alarm_card(
                definition.card_key,
                definition.event_id,
                definition.tone,
                definition=definition,
                include_button=True,
            )
        ],
        className='reference-ada__alarm-card-slot',
    )


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
                        build_reference_alarm_card(
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


def build_reference_alarm_card(
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


def _subcomponent_target_definition(key: str) -> AlarmBaselineTarget:
    return AlarmBaselineTarget(AlarmBaselineTargetKind.SUBCOMPONENT, key)


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
