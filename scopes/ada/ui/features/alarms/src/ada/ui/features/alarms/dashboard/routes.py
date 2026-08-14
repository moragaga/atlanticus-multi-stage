from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from ..errors import AlarmDefinitionError
from .baseline import AlarmBaselineTarget

_CARD_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


class AlarmRouteTone(StrEnum):
    CRITICAL = 'critical'
    ATTENTION = 'attention'


@dataclass(frozen=True, slots=True)
class AlarmDashboardRouteDefinition:
    event_id: str
    assignment_key: str
    card_key: str
    origin: AlarmBaselineTarget
    impacts: tuple[AlarmBaselineTarget, ...]
    tone: AlarmRouteTone

    def __post_init__(self) -> None:
        _validate_identity(self.event_id, 'event id')
        _validate_identity(self.assignment_key, 'assignment key')
        _validate_card_key(self.card_key)
        if not isinstance(self.origin, AlarmBaselineTarget):
            raise AlarmDefinitionError(f'Invalid alarm route origin: {self.origin!r}')
        object.__setattr__(self, 'impacts', tuple(self.impacts))
        if not self.impacts:
            raise AlarmDefinitionError('Alarm route requires at least one impact target')
        if any(not isinstance(target, AlarmBaselineTarget) for target in self.impacts):
            raise AlarmDefinitionError('Alarm route contains an invalid impact target')
        identities = [(target.kind, target.key) for target in self.impacts]
        if len(identities) != len(set(identities)):
            raise AlarmDefinitionError('Alarm route contains duplicate impact targets')
        if not isinstance(self.tone, AlarmRouteTone):
            raise AlarmDefinitionError(f'Invalid alarm route tone: {self.tone!r}')


def alarm_card_identity_attributes(card_key: str) -> dict[str, str]:
    _validate_card_key(card_key)
    return {'data-ada-alarm-card-key': card_key}


def alarm_card_presentation_attributes(
    definition: AlarmDashboardRouteDefinition,
    *,
    distributed: bool = False,
) -> dict[str, str]:
    if not isinstance(definition, AlarmDashboardRouteDefinition):
        raise AlarmDefinitionError(f'Invalid alarm route definition: {definition!r}')
    if not isinstance(distributed, bool):
        raise AlarmDefinitionError(f'Invalid distributed alarm flag: {distributed!r}')
    impacts = '|'.join(f'{target.kind.value}:{target.key}' for target in definition.impacts)
    return {
        **alarm_card_identity_attributes(definition.card_key),
        'data-ada-alarm-event-id': definition.event_id,
        'data-ada-alarm-assignment-key': definition.assignment_key,
        'data-ada-alarm-card-tone': definition.tone.value,
        'data-ada-alarm-route-origin': (f'{definition.origin.kind.value}:{definition.origin.key}'),
        'data-ada-alarm-route-impacts': impacts,
        'data-ada-alarm-distributed': str(distributed).lower(),
        'data-ada-alarm-selected': 'false',
    }


def _validate_card_key(value: str) -> None:
    if not isinstance(value, str) or not _CARD_KEY_PATTERN.fullmatch(value):
        raise AlarmDefinitionError(f'Invalid alarm card key: {value!r}')


def _validate_identity(value: str, label: str) -> None:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise AlarmDefinitionError(f'Invalid alarm {label}: {value!r}')
