# Espejo pedagógico de los builders Dash del dashboard de alarmas.
# Baseline permanente y una superficie de ruta reutilizable por scope.
from __future__ import annotations

from dash import html

from .baseline import AlarmBaselineDefinition
from .routes import AlarmDashboardRouteDefinition


def build_alarm_dashboard_baseline(
    definition: AlarmBaselineDefinition,
    *,
    class_name: str | None = None,
) -> html.Div:
    classes = ' '.join(
        item
        for item in (
            'ada-alarm-dashboard-baseline',
            f'ada-alarm-dashboard-baseline--{definition.layout.value}',
            class_name,
        )
        if item
    )
    return html.Div(
        className=classes,
        children=[
            html.Div(className='ada-alarm-dashboard-baseline__line'),
            *(_build_node(target.kind.value, target.key) for target in definition.targets),
        ],
        **{
            'aria-hidden': 'true',
            'data-ada-alarm-baseline': definition.layout.value,
        },
    )


# Una sola superficie evita un renderer/observer por cada alarma visible.
def build_alarm_dashboard_route_layer(
    definition: AlarmDashboardRouteDefinition | None = None,
) -> html.Div:
    attributes = {
        'aria-hidden': 'true',
        'data-ada-alarm-route': 'active',
        'data-ada-alarm-route-state': 'idle',
        'data-ada-alarm-route-replay': '0',
    }
    if definition is not None:
        impacts = '|'.join(
            f'{target.kind.value}:{target.key}' for target in definition.impacts
        )
        attributes.update(
            {
                'data-ada-alarm-route-event-id': definition.event_id,
                'data-ada-alarm-route-assignment-key': definition.assignment_key,
                'data-ada-alarm-route-card-key': definition.card_key,
                'data-ada-alarm-route-origin': (
                    f'{definition.origin.kind.value}:{definition.origin.key}'
                ),
                'data-ada-alarm-route-impacts': impacts,
                'data-ada-alarm-route-tone': definition.tone.value,
                'data-ada-alarm-route-state': 'active',
                'data-ada-alarm-route-replay': '1',
            }
        )
    return html.Div(
        html.Span(className='ada-alarm-dashboard-route__measure'),
        className='ada-alarm-dashboard-route',
        **attributes,
    )


def build_integrated_operations_alarm_baseline(
    component_keys: tuple[str, ...],
    *,
    class_name: str | None = None,
) -> html.Div:
    return build_alarm_dashboard_baseline(
        AlarmBaselineDefinition.integrated_operations(component_keys),
        class_name=class_name,
    )


def build_process_alarm_baseline(*, class_name: str | None = None) -> html.Div:
    return build_alarm_dashboard_baseline(
        AlarmBaselineDefinition.process(),
        class_name=class_name,
    )


# Dot y chevrons comparten caja fija: el estado visual no cambia geometría.
def _build_node(target_kind: str, target_key: str) -> html.Span:
    return html.Span(
        [
            html.Span(className='ada-alarm-dashboard-baseline__node-dot'),
            html.Span(
                className=(
                    'ada-alarm-dashboard-baseline__node-chevron '
                    'ada-alarm-dashboard-baseline__node-chevron--up'
                )
            ),
            html.Span(
                className=(
                    'ada-alarm-dashboard-baseline__node-chevron '
                    'ada-alarm-dashboard-baseline__node-chevron--down'
                )
            ),
        ],
        className='ada-alarm-dashboard-baseline__node',
        **{
            'data-ada-alarm-target-kind': target_kind,
            'data-ada-alarm-target-key': target_key,
            'data-ada-alarm-positioned': 'false',
            'data-ada-alarm-node-state': 'neutral',
        },
    )
