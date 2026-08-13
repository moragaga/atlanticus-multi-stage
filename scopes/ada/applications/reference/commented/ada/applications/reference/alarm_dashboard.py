# Harness pedagógico para validar placement y geometría antes de conectar el motor real.
from dash import html

from ada.ui.features.alarms.dashboard import (
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

# IO conserva la misma geometría horizontal entre las alarm cards y sus componentes.
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
# Process reserva seis slots horizontales fijos, independientemente de cuántas alarmas haya.
_PROCESS_ALARM_COUNT = 6
_PROCESS_ACTIVE_ALARM_INDEX = 2


def build_reference_alarm_dashboard_baselines() -> html.Section:
    return html.Section(
        [
            html.H2('Alarm Dashboard Geometry'),
            html.P('Baseline permanente y placement visual de referencia sin motor de alarmas.'),
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
        ],
        className='reference-ada__alarm-baselines',
    )


def _build_integrated_operations_same_point_reference() -> html.Div:
    target = _component_target_definition('general_mine')
    route = AlarmDashboardRouteDefinition(
        route_key='io_same_point',
        card_key='io_same_point_alarm',
        origin=target,
        impacts=(target,),
        tone=AlarmRouteTone.CRITICAL,
    )
    return _build_integrated_operations_scope(
        'Mismo punto · card alineada con General Mina',
        route,
        {'general_mine': ('io_same_point_alarm', 'Origen e impacto')},
    )


def _build_integrated_operations_span_reference() -> html.Div:
    route = AlarmDashboardRouteDefinition(
        route_key='io_origin_to_impacts',
        card_key='io_loading_alarm',
        origin=_component_target_definition('loading'),
        impacts=(
            _component_target_definition('flotation'),
            _component_target_definition('port'),
        ),
        tone=AlarmRouteTone.ATTENTION,
    )
    return _build_integrated_operations_scope(
        'Máximo visible de referencia · 3 Mina + 3 Planta',
        route,
        {
            'general_mine': ('io_general_mine_alarm', 'General Mina'),
            'loading': ('io_loading_alarm', 'Carguío'),
            'transport': ('io_transport_alarm', 'Transporte'),
            'crushing_stmg': ('io_crushing_alarm', 'Chancado-STMG'),
            'flotation': ('io_flotation_alarm', 'Flotación'),
            'port': ('io_port_alarm', 'Puerto'),
        },
    )


# La baseline vive fuera de los frames internos; cards y body comparten el mismo padding.
def _build_integrated_operations_scope(
    label: str,
    route: AlarmDashboardRouteDefinition,
    alarm_cards: dict[str, tuple[str, str]],
) -> html.Div:
    component_keys = tuple(key for key, _ in _IO_COMPONENTS)
    return html.Div(
        [
            html.Div(label, className='reference-ada__alarm-example-label'),
            html.Div(
                _build_integrated_operations_alarm_grid(alarm_cards),
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


# La grilla superior replica exactamente las columnas de IO para conservar X y ancho del target.
def _build_integrated_operations_alarm_grid(
    alarm_cards: dict[str, tuple[str, str]],
) -> html.Div:
    return html.Div(
        [
            _io_alarm_slot('general_mine', alarm_cards),
            html.Div(
                [
                    _io_alarm_slot('loading', alarm_cards),
                    _io_alarm_slot('transport', alarm_cards),
                ],
                className='reference-ada__alarm-io-double',
            ),
            *(
                _io_alarm_slot(key, alarm_cards)
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


def _io_alarm_slot(
    component_key: str,
    alarm_cards: dict[str, tuple[str, str]],
) -> html.Div:
    alarm = alarm_cards.get(component_key)
    children = [] if alarm is None else [_reference_alarm_card(*alarm)]
    return html.Div(children, className='reference-ada__alarm-card-slot')


# Process desacopla placement de cards (6 slots) del target operacional (center).
def _build_process_reference(variant: str, slots: tuple[str, ...]) -> html.Div:
    center = AlarmBaselineTarget(AlarmBaselineTargetKind.SLOT, 'center')
    prefix = f'process_{variant.replace("-", "_")}'
    route = AlarmDashboardRouteDefinition(
        route_key=prefix,
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
                _build_process_alarm_grid(prefix),
                className='reference-ada__alarm-content-frame',
            ),
            build_alarm_dashboard_route_layer(route),
            build_process_alarm_baseline(),
            html.Div(
                html.Div(
                    [_slot_target(slot, slot.title()) for slot in slots],
                    className=(
                        'reference-ada__alarm-process-grid '
                        f'reference-ada__alarm-process-grid--{variant}'
                    ),
                ),
                className='reference-ada__alarm-body-frame',
            ),
        ],
        className='reference-ada__alarm-geometry-scope',
        **alarm_geometry_scope_attributes(),
    )


# Los seis slots permanecen montados para evitar cambios de tamaño durante la rotación.
def _build_process_alarm_grid(prefix: str) -> html.Div:
    return html.Div(
        [
            _reference_alarm_card(f'{prefix}_alarm_{index}', f'Alarma {index}')
            for index in range(1, _PROCESS_ALARM_COUNT + 1)
        ],
        className='reference-ada__alarm-process-placement-grid',
    )


def _reference_alarm_card(card_key: str, label: str) -> html.Div:
    return html.Div(
        [
            html.Div('ALARM', className='reference-ada__alarm-card-band'),
            html.Div(label, className='reference-ada__alarm-card-body'),
        ],
        className='reference-ada__alarm-card',
        **{
            **alarm_card_identity_attributes(card_key),
            'data-ada-alarm-active': 'false',
        },
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
