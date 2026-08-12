# Espejo comentado: conserva exactamente la lógica productiva del módulo.
# Los comentarios describen la responsabilidad sin alterar el AST ejecutable.
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum

from ada.contracts.tool_manifest import ToolScope
from ada.ui.branding import BrandState
from ada.ui.components.global_indicator import GlobalIndicatorData

from .errors import HeaderDefinitionError

_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


class HeaderTone(StrEnum):
    NEUTRAL = 'neutral'
    ATTENTION = 'attention'
    CRITICAL = 'critical'


@dataclass(frozen=True, slots=True)
class HeaderGlobalIndicator:
    key: str
    section_key: str
    scope: ToolScope
    indicator: GlobalIndicatorData
    definition_key: str | None = None

    def __post_init__(self) -> None:
        _require_key(self.key, field_name='indicator key')
        _require_key(self.section_key, field_name='indicator section_key')
        if self.definition_key is not None:
            _require_key(self.definition_key, field_name='indicator definition_key')


@dataclass(frozen=True, slots=True)
class AlarmManagementSegmentState:
    section_key: str
    scope: ToolScope
    group_value: str
    management_percentage: float
    tone: HeaderTone = HeaderTone.NEUTRAL

    def __post_init__(self) -> None:
        _require_key(self.section_key, field_name='alarm management section_key')
        _require_text(self.group_value, field_name='alarm management group_value')
        if self.scope is ToolScope.GLOBAL:
            raise HeaderDefinitionError('Alarm management segment must be mine or plant')
        if not 0 <= self.management_percentage <= 100:
            raise HeaderDefinitionError('Alarm management percentage must be between 0 and 100')


@dataclass(frozen=True, slots=True)
class AlarmManagementState:
    segments: tuple[AlarmManagementSegmentState, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'segments', tuple(self.segments))
        if not self.segments:
            raise HeaderDefinitionError('Alarm management requires at least one segment')
        scope_values = [item.scope for item in self.segments]
        if len(scope_values) != len(set(scope_values)):
            raise HeaderDefinitionError('Alarm management contains duplicate scopes')


@dataclass(frozen=True, slots=True)
class AlarmStatusState:
    active_count: int
    managed_count: int

    def __post_init__(self) -> None:
        if self.active_count < 0 or self.managed_count < 0:
            raise HeaderDefinitionError('Alarm status counts cannot be negative')


@dataclass(frozen=True, slots=True)
class HeaderBrandState:
    brand: BrandState
    application_name: str
    tool_name: str
    assistant_label: str = 'Asistente de decisiones ágiles'

    def __post_init__(self) -> None:
        _require_text(self.application_name, field_name='application_name')
        _require_text(self.tool_name, field_name='tool_name')
        _require_text(self.assistant_label, field_name='assistant_label')


@dataclass(frozen=True, slots=True)
class HeaderState:
    tool_key: str
    brand: HeaderBrandState
    global_indicators: tuple[HeaderGlobalIndicator, ...] = field(default_factory=tuple)
    alarm_management: AlarmManagementState | None = None
    alarm_status: AlarmStatusState | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, 'global_indicators', tuple(self.global_indicators))
        _require_key(self.tool_key, field_name='tool_key')
        keys = [indicator.key for indicator in self.global_indicators]
        if len(keys) != len(set(keys)):
            raise HeaderDefinitionError('Header contains duplicate global indicator keys')


def _require_key(value: str, *, field_name: str) -> None:
    if not _KEY_PATTERN.fullmatch(value):
        raise HeaderDefinitionError(f'Invalid {field_name}: {value!r}')


def _require_text(value: str, *, field_name: str) -> None:
    if not value.strip():
        raise HeaderDefinitionError(f'{field_name} cannot be empty')
