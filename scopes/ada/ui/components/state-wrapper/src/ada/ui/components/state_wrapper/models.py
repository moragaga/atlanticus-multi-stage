from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from .errors import StateWrapperDefinitionError

_CLASS_TOKEN = re.compile(r'^[A-Za-z_][A-Za-z0-9_-]*$')
_READY_NAME = re.compile(r'^[a-z][a-z0-9-]*$')


class CoverState(StrEnum):
    NONE = 'none'
    CONSTRUCTION = 'construction'
    STALE = 'stale'
    SOURCE_ERROR = 'source-error'
    COMPONENT_ERROR = 'component-error'


@dataclass(frozen=True, slots=True)
class ComponentCover:
    state: CoverState = CoverState.NONE
    message: str | None = None
    icon_class: str | None = None

    def __post_init__(self) -> None:
        has_overlay_content = self.message is not None or self.icon_class is not None
        if self.state is CoverState.NONE and has_overlay_content:
            raise StateWrapperDefinitionError('Uncovered component cannot declare overlay content')
        if self.message is not None and not self.message.strip():
            raise StateWrapperDefinitionError('State wrapper message cannot be empty')
        if self.icon_class is not None:
            _require_class_tokens(self.icon_class)

    @classmethod
    def none(cls) -> 'ComponentCover':
        return cls()

    @classmethod
    def stale(
        cls,
        *,
        message: str = 'Datos desactualizados',
        icon_class: str = 'bi bi-cloud-slash',
    ) -> 'ComponentCover':
        return cls(CoverState.STALE, message, icon_class)

    @classmethod
    def construction(
        cls,
        *,
        message: str = 'En construcción',
        icon_class: str = 'bi bi-hammer',
    ) -> 'ComponentCover':
        return cls(CoverState.CONSTRUCTION, message, icon_class)

    @classmethod
    def source_error(
        cls,
        *,
        message: str = 'Problemas con la fuente de datos',
        icon_class: str = 'bi bi-cloud-slash',
    ) -> 'ComponentCover':
        return cls(CoverState.SOURCE_ERROR, message, icon_class)

    @classmethod
    def component_error(
        cls,
        *,
        message: str = 'No fue posible mostrar este componente',
        icon_class: str = 'bi bi-exclamation-triangle',
    ) -> 'ComponentCover':
        return cls(CoverState.COMPONENT_ERROR, message, icon_class)

    @property
    def covered(self) -> bool:
        return self.state is not CoverState.NONE


def normalize_ready_name(value: str) -> str:
    normalized = value.strip()
    if not _READY_NAME.fullmatch(normalized):
        raise StateWrapperDefinitionError(f'Invalid readiness name: {value!r}')
    return normalized


def _require_class_tokens(value: str) -> None:
    tokens = value.split()
    if not tokens or not all(_CLASS_TOKEN.fullmatch(token) for token in tokens):
        raise StateWrapperDefinitionError(f'Invalid state wrapper CSS classes: {value!r}')
