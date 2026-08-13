from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from ..errors import AlarmDefinitionError
from .baseline import AlarmBaselineTarget

_ROUTE_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


class AlarmRouteTone(StrEnum):
    CRITICAL = 'critical'
    ATTENTION = 'attention'


@dataclass(frozen=True, slots=True)
class AlarmDashboardRouteDefinition:
    route_key: str
    card_key: str
    origin: AlarmBaselineTarget
    impacts: tuple[AlarmBaselineTarget, ...]
    tone: AlarmRouteTone

    def __post_init__(self) -> None:
        _validate_route_key(self.route_key, 'route')
        _validate_route_key(self.card_key, 'card')
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
    _validate_route_key(card_key, 'card')
    return {'data-ada-alarm-card-key': card_key}


def _validate_route_key(value: str, label: str) -> None:
    if not isinstance(value, str) or not _ROUTE_KEY_PATTERN.fullmatch(value):
        raise AlarmDefinitionError(f'Invalid alarm {label} key: {value!r}')
