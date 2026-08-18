from __future__ import annotations

import re
from collections.abc import Mapping

from dash import html

from ada.features.alarms.core.dashboard.baseline import AlarmBaselineDefinition
from ada.features.alarms.core.errors import AlarmDefinitionError
from ada.features.alarms.runtime.dashboard.routes import AlarmDashboardRouteDefinition

_SCOPE_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


def build_alarm_dashboard_baseline(
    definition: AlarmBaselineDefinition,
    *,
    class_name: str | None = None,
    target_scopes: Mapping[str, str] | None = None,
) -> html.Div:
    scopes = _validated_target_scopes(definition, target_scopes)
    classes = ' '.join(
        item
        for item in (
            'ada-alarm-dashboard-baseline',
            f'ada-alarm-dashboard-baseline--{definition.layout.value}',
            'ada-alarm-dashboard-baseline--scoped' if scopes is not None else None,
            class_name,
        )
        if item
    )
    children = [html.Div(className='ada-alarm-dashboard-baseline__line')]
    if scopes is not None:
        children.append(html.Span(className='ada-alarm-dashboard-baseline__scope-divider'))
    children.extend(
        _build_node(
            target.kind.value,
            target.key,
            scope=None if scopes is None else scopes[target.key],
        )
        for target in definition.targets
    )
    attributes = {
        'aria-hidden': 'true',
        'data-ada-alarm-baseline': definition.layout.value,
    }
    if scopes is not None:
        attributes['data-ada-alarm-scoped'] = 'true'
    return html.Div(
        className=classes,
        children=children,
        **attributes,
    )


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
        destinations = '|'.join(
            f'{target.kind.value}:{target.key}' for target in definition.destinations
        )
        affected_targets = '|'.join(
            f'{target.kind.value}:{target.key}' for target in definition.affected_targets
        )
        attributes.update(
            {
                'data-ada-alarm-route-event-id': definition.event_id,
                'data-ada-alarm-route-assignment-key': definition.assignment_key,
                'data-ada-alarm-route-placement-key': definition.placement_key,
                'data-ada-alarm-route-card-key': definition.card_key,
                'data-ada-alarm-route-origin': (
                    f'{definition.origin.kind.value}:{definition.origin.key}'
                ),
                'data-ada-alarm-route-destinations': destinations,
                'data-ada-alarm-affected-targets': affected_targets,
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
    component_scopes: Mapping[str, str] | None = None,
) -> html.Div:
    return build_alarm_dashboard_baseline(
        AlarmBaselineDefinition.integrated_operations(component_keys),
        class_name=class_name,
        target_scopes=component_scopes,
    )


def build_process_alarm_baseline(*, class_name: str | None = None) -> html.Div:
    return build_alarm_dashboard_baseline(
        AlarmBaselineDefinition.process(),
        class_name=class_name,
    )


def _build_node(target_kind: str, target_key: str, *, scope: str | None = None) -> html.Span:
    attributes = {
        'data-ada-alarm-target-kind': target_kind,
        'data-ada-alarm-target-key': target_key,
        'data-ada-alarm-positioned': 'false',
        'data-ada-alarm-node-state': 'neutral',
    }
    if scope is not None:
        attributes['data-ada-alarm-scope'] = scope
        attributes['data-scope'] = scope
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
        **attributes,
    )


def _validated_target_scopes(
    definition: AlarmBaselineDefinition,
    target_scopes: Mapping[str, str] | None,
) -> dict[str, str] | None:
    if target_scopes is None:
        return None
    scopes = dict(target_scopes)
    target_keys = {target.key for target in definition.targets}
    if set(scopes) != target_keys:
        raise AlarmDefinitionError('Alarm baseline scope mapping must match baseline targets')
    invalid_scope = any(
        not isinstance(scope, str) or not _SCOPE_PATTERN.fullmatch(scope)
        for scope in scopes.values()
    )
    if invalid_scope:
        raise AlarmDefinitionError('Alarm baseline contains an invalid presentation scope')
    return scopes
