from dash import html

from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST, ToolSectionKind
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

_IO_COMPONENTS = tuple(
    (component.key, component.display_name)
    for scope_key in ('mine', 'plant')
    for component in INTEGRATED_OPERATIONS_MANIFEST.children(scope_key)
    if component.kind is ToolSectionKind.COMPONENT
)
_IO_SUBCOMPONENTS = {
    component_key: tuple(
        (section.key, section.display_name)
        for section in INTEGRATED_OPERATIONS_MANIFEST.children(component_key)
        if section.kind is ToolSectionKind.SUBCOMPONENT
    )
    for component_key, _ in _IO_COMPONENTS
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
        'general_mina': _route_definition(
            event_id='io-player-general-mina-001',
            assignment_key='component:general_mina',
            placement_key='io-general-mina-slot-1',
            card_key='io_player_general_mina_001',
            origin=_component_target_definition('general_mina'),
            destinations=(_component_target_definition('general_mina'),),
            affected_targets=(_io_subcomponent_target('general_mina', 'movimiento_mina'),),
            tone=AlarmRouteTone.CRITICAL,
        ),
        'carguio': _route_definition(
            event_id='io-player-carguio-001',
            assignment_key='component:carguio',
            placement_key='io-carguio-slot-1',
            card_key='io_player_carguio_001',
            origin=_component_target_definition('carguio'),
            destinations=(
                _component_target_definition('flotacion'),
                _component_target_definition('transporte_fluidos'),
                _component_target_definition('puerto'),
            ),
            affected_targets=(
                _io_subcomponent_target('flotacion', 'selectiva'),
                _io_subcomponent_target('transporte_fluidos', 'stc'),
                _io_subcomponent_target('puerto', 'desaladora'),
            ),
            tone=AlarmRouteTone.ATTENTION,
        ),
        'transporte': _route_definition(
            event_id='io-player-transporte-001',
            assignment_key='component:transporte',
            placement_key='io-transporte-slot-1',
            card_key='io_player_transporte_001',
            origin=_component_target_definition('transporte'),
            destinations=(_component_target_definition('transporte'),),
            affected_targets=(_io_subcomponent_target('transporte', 'numero_operativos'),),
            tone=AlarmRouteTone.CRITICAL,
        ),
        'chancado_stmg': _route_definition(
            event_id='io-player-chancado-001',
            assignment_key='component:chancado_stmg',
            placement_key='io-chancado-stmg-slot-1',
            card_key='io_player_chancado_001',
            origin=_component_target_definition('chancado_stmg'),
            destinations=(_component_target_definition('chancado_stmg'),),
            affected_targets=(_io_subcomponent_target('chancado_stmg', 'chancado_stmg'),),
            tone=AlarmRouteTone.CRITICAL,
        ),
        'flotacion': _route_definition(
            event_id='io-player-flotacion-001',
            assignment_key='component:flotacion',
            placement_key='io-flotacion-slot-1',
            card_key='io_player_flotacion_001',
            origin=_component_target_definition('flotacion'),
            destinations=(
                _component_target_definition('molienda'),
                _component_target_definition('flotacion'),
            ),
            affected_targets=(
                _io_subcomponent_target('molienda', 'molienda'),
                _component_target_definition('flotacion'),
            ),
            tone=AlarmRouteTone.ATTENTION,
        ),
        'puerto': _route_definition(
            event_id='io-player-puerto-001',
            assignment_key='component:puerto',
            placement_key='io-puerto-slot-1',
            card_key='io_player_puerto_001',
            origin=_component_target_definition('puerto'),
            destinations=(_component_target_definition('puerto'),),
            affected_targets=(_io_subcomponent_target('puerto', 'puerto'),),
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


def _io_subcomponent_target(component: str, subcomponent: str) -> AlarmBaselineTarget:
    section = INTEGRATED_OPERATIONS_MANIFEST.subcomponent(
        component=component,
        subcomponent=subcomponent,
    )
    return _subcomponent_target_definition(section.key)


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
