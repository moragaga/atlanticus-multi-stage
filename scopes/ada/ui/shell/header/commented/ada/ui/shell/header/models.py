# Este espejo explica el contrato de estado del indicador global sin alterar su AST.
# Las mediciones normales se identifican por key y label; el texto visible no gobierna el mapping.
# La capacidad de tres filas es una regla visual común para todos los Headers ADA.
# Last measurement se mantiene separado y opcional porque su presentación es distinta.
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ada.contracts.tool_manifest import ToolScope
from ada.ui.components.branding import BrandState
from ada.ui.components.global_indicator import GlobalIndicatorState
from ada.ui.components.state_wrapper import ComponentCover

from .errors import HeaderDefinitionError

_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
_INDICATOR_SCOPES = frozenset({ToolScope.MINE, ToolScope.PLANT})


@dataclass(frozen=True, slots=True)
class HeaderIndicatorPlacement:
    section_key: str
    scopes: frozenset[ToolScope]
    indicator: GlobalIndicatorState

    def __post_init__(self) -> None:
        object.__setattr__(self, 'scopes', frozenset(self.scopes))
        _require_key(self.section_key, field_name='indicator section_key')
        if not self.scopes:
            raise HeaderDefinitionError('Global indicator placement requires at least one scope')
        if not self.scopes <= _INDICATOR_SCOPES:
            raise HeaderDefinitionError(
                'Global indicator placement supports only mine and plant scopes'
            )


@dataclass(frozen=True, slots=True)
class HeaderBrandState:
    resolved_brand: BrandState
    application_name: str
    tool_name: str
    assistant_label: str = 'Asistente de decisiones ágiles'

    def __post_init__(self) -> None:
        _require_text(self.application_name, field_name='application_name')
        _require_text(self.tool_name, field_name='tool_name')
        _require_text(self.assistant_label, field_name='assistant_label')


@dataclass(frozen=True, slots=True)
class HeaderSectionStates:
    global_indicators: ComponentCover = field(default_factory=ComponentCover.none)


@dataclass(frozen=True, slots=True)
class HeaderState:
    tool_key: str
    brand: HeaderBrandState
    global_indicators: tuple[HeaderIndicatorPlacement, ...] = field(default_factory=tuple)
    section_states: HeaderSectionStates = field(default_factory=HeaderSectionStates)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'global_indicators', tuple(self.global_indicators))
        _require_key(self.tool_key, field_name='tool_key')
        keys = [placement.indicator.key for placement in self.global_indicators]
        if len(keys) != len(set(keys)):
            raise HeaderDefinitionError('Header contains duplicate global indicator keys')


def _require_key(value: str, *, field_name: str) -> None:
    if not _KEY_PATTERN.fullmatch(value):
        raise HeaderDefinitionError(f'Invalid {field_name}: {value!r}')


def _require_text(value: str, *, field_name: str) -> None:
    if not value.strip():
        raise HeaderDefinitionError(f'{field_name} cannot be empty')
