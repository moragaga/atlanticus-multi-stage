from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from ada.contracts.tool_manifest import ToolScope
from ada.features.alarms.core.errors import AlarmDefinitionError

_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


class AlarmManagementSummaryTone(StrEnum):
    NEUTRAL = 'neutral'
    ATTENTION = 'attention'
    CRITICAL = 'critical'


@dataclass(frozen=True, slots=True)
class AlarmManagementSummarySegmentState:
    section_key: str
    scope: ToolScope
    group: str
    management_percentage: float
    tone: AlarmManagementSummaryTone = AlarmManagementSummaryTone.NEUTRAL

    def __post_init__(self) -> None:
        if not _KEY_PATTERN.fullmatch(self.section_key):
            raise AlarmDefinitionError(
                f'Invalid alarm management summary section_key: {self.section_key!r}'
            )
        if not self.group.strip():
            raise AlarmDefinitionError('Alarm management summary group cannot be empty')
        if self.scope is ToolScope.GLOBAL:
            raise AlarmDefinitionError('Alarm management summary segment must be mine or plant')
        if not 0 <= self.management_percentage <= 100:
            raise AlarmDefinitionError(
                'Alarm management summary percentage must be between 0 and 100'
            )


@dataclass(frozen=True, slots=True)
class AlarmManagementSummaryState:
    segments: tuple[AlarmManagementSummarySegmentState, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'segments', tuple(self.segments))
        if not self.segments:
            raise AlarmDefinitionError('Alarm management summary requires at least one segment')
        scopes = [segment.scope for segment in self.segments]
        if len(scopes) != len(set(scopes)):
            raise AlarmDefinitionError('Alarm management summary contains duplicate scopes')
