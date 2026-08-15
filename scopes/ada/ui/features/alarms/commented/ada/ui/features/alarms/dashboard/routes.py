# Espejo pedagógico del contrato de una alarma presentable.
# event_id es identidad; assignment_key es posición semántica y nunca sustituye al evento.
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


# DTO de presentación: separa el recorrido sobre el baseline de los elementos del body.
@dataclass(frozen=True, slots=True)
class AlarmDashboardRouteDefinition:
    event_id: str
    assignment_key: str
    placement_key: str
    card_key: str
    origin: AlarmBaselineTarget
    destinations: tuple[AlarmBaselineTarget, ...]
    affected_targets: tuple[AlarmBaselineTarget, ...]
    tone: AlarmRouteTone

    def __post_init__(self) -> None:
        _validate_identity(self.event_id, 'event id')
        _validate_identity(self.assignment_key, 'assignment key')
        _validate_identity(self.placement_key, 'placement key')
        _validate_card_key(self.card_key)
        if not isinstance(self.origin, AlarmBaselineTarget):
            raise AlarmDefinitionError(f'Invalid alarm route origin: {self.origin!r}')
        object.__setattr__(self, 'destinations', tuple(self.destinations))
        object.__setattr__(self, 'affected_targets', tuple(self.affected_targets))
        _validate_targets(self.destinations, 'route destination')
        _validate_targets(self.affected_targets, 'affected')
        if not isinstance(self.tone, AlarmRouteTone):
            raise AlarmDefinitionError(f'Invalid alarm route tone: {self.tone!r}')


def alarm_card_identity_attributes(card_key: str) -> dict[str, str]:
    _validate_card_key(card_key)
    return {'data-ada-alarm-card-key': card_key}


# Serializamos semántica al DOM; la geometría física se resuelve clientside contra targets reales.
def alarm_card_presentation_attributes(
    definition: AlarmDashboardRouteDefinition,
    *,
    distributed: bool = False,
) -> dict[str, str]:
    if not isinstance(definition, AlarmDashboardRouteDefinition):
        raise AlarmDefinitionError(f'Invalid alarm route definition: {definition!r}')
    if not isinstance(distributed, bool):
        raise AlarmDefinitionError(f'Invalid distributed alarm flag: {distributed!r}')
    destinations = '|'.join(
        f'{target.kind.value}:{target.key}' for target in definition.destinations
    )
    affected_targets = '|'.join(
        f'{target.kind.value}:{target.key}' for target in definition.affected_targets
    )
    return {
        **alarm_card_identity_attributes(definition.card_key),
        'data-ada-alarm-event-id': definition.event_id,
        'data-ada-alarm-assignment-key': definition.assignment_key,
        # El scheduler cambia placement_key solo cuando confirma una rotación visual.
        'data-ada-alarm-placement-key': definition.placement_key,
        'data-ada-alarm-card-tone': definition.tone.value,
        'data-ada-alarm-route-origin': (f'{definition.origin.kind.value}:{definition.origin.key}'),
        'data-ada-alarm-route-destinations': destinations,
        'data-ada-alarm-affected-targets': affected_targets,
        'data-ada-alarm-distributed': str(distributed).lower(),
        'data-ada-alarm-selected': 'false',
    }


def _validate_card_key(value: str) -> None:
    if not isinstance(value, str) or not _CARD_KEY_PATTERN.fullmatch(value):
        raise AlarmDefinitionError(f'Invalid alarm card key: {value!r}')


def _validate_identity(value: str, label: str) -> None:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise AlarmDefinitionError(f'Invalid alarm {label}: {value!r}')


# Ambos grupos son explícitos y no admiten vacíos, tipos ajenos ni identidades repetidas.
def _validate_targets(targets: tuple[AlarmBaselineTarget, ...], label: str) -> None:
    if not targets:
        raise AlarmDefinitionError(f'Alarm route requires at least one {label} target')
    if any(not isinstance(target, AlarmBaselineTarget) for target in targets):
        raise AlarmDefinitionError(f'Alarm route contains an invalid {label} target')
    identities = [(target.kind, target.key) for target in targets]
    if len(identities) != len(set(identities)):
        raise AlarmDefinitionError(f'Alarm route contains duplicate {label} targets')
