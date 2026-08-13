from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from ..errors import AlarmDefinitionError

_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


class AlarmBaselineLayout(StrEnum):
    INTEGRATED_OPERATIONS = 'integrated-operations'
    PROCESS = 'process'


class AlarmBaselineTargetKind(StrEnum):
    COMPONENT = 'component'
    SLOT = 'slot'


@dataclass(frozen=True, slots=True)
class AlarmBaselineTarget:
    kind: AlarmBaselineTargetKind
    key: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, AlarmBaselineTargetKind):
            raise AlarmDefinitionError(f'Invalid alarm baseline target kind: {self.kind!r}')
        validate_alarm_target_key(self.key)


@dataclass(frozen=True, slots=True)
class AlarmBaselineDefinition:
    layout: AlarmBaselineLayout
    targets: tuple[AlarmBaselineTarget, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.layout, AlarmBaselineLayout):
            raise AlarmDefinitionError(f'Invalid alarm baseline layout: {self.layout!r}')
        object.__setattr__(self, 'targets', tuple(self.targets))
        if not self.targets:
            raise AlarmDefinitionError('Alarm baseline requires at least one target')
        identities = [(target.kind, target.key) for target in self.targets]
        if len(identities) != len(set(identities)):
            raise AlarmDefinitionError('Alarm baseline contains duplicate targets')

    @classmethod
    def integrated_operations(
        cls,
        component_keys: tuple[str, ...],
    ) -> AlarmBaselineDefinition:
        return cls(
            layout=AlarmBaselineLayout.INTEGRATED_OPERATIONS,
            targets=tuple(
                AlarmBaselineTarget(AlarmBaselineTargetKind.COMPONENT, key)
                for key in component_keys
            ),
        )

    @classmethod
    def process(cls) -> AlarmBaselineDefinition:
        return cls(
            layout=AlarmBaselineLayout.PROCESS,
            targets=(AlarmBaselineTarget(AlarmBaselineTargetKind.SLOT, 'center'),),
        )


def validate_alarm_target_key(value: str) -> None:
    if not isinstance(value, str) or not _KEY_PATTERN.fullmatch(value):
        raise AlarmDefinitionError(f'Invalid alarm target key: {value!r}')
