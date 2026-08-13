# Espejo comentado de la implementación productiva.
# Mantiene exactamente el mismo contrato y comportamiento del archivo en src/.
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from .errors import StateWrapperDefinitionError

_CLASS_TOKEN = re.compile(r'^[A-Za-z_][A-Za-z0-9_-]*$')


class ComponentAvailability(StrEnum):
    READY = 'ready'
    CONSTRUCTION = 'construction'


class DataFreshness(StrEnum):
    FRESH = 'fresh'
    STALE = 'stale'


@dataclass(frozen=True, slots=True)
class StateWrapperState:
    availability: ComponentAvailability = ComponentAvailability.READY
    freshness: DataFreshness = DataFreshness.FRESH
    message: str | None = None
    icon_class: str | None = None

    def __post_init__(self) -> None:
        if (
            self.availability is ComponentAvailability.CONSTRUCTION
            and self.freshness is DataFreshness.STALE
        ):
            raise StateWrapperDefinitionError(
                'Construction state cannot declare stale data freshness'
            )
        if self.message is not None and not self.message.strip():
            raise StateWrapperDefinitionError('State wrapper message cannot be empty')
        if self.icon_class is not None:
            _require_class_tokens(self.icon_class)

    @classmethod
    def ready(cls) -> StateWrapperState:
        return cls()

    @classmethod
    def stale(
        cls,
        *,
        message: str = 'Datos desactualizados',
        icon_class: str = 'bi bi-cloud-slash',
    ) -> StateWrapperState:
        return cls(
            freshness=DataFreshness.STALE,
            message=message,
            icon_class=icon_class,
        )

    @classmethod
    def construction(
        cls,
        *,
        message: str = 'En construcción',
        icon_class: str = 'bi bi-hammer',
    ) -> StateWrapperState:
        return cls(
            availability=ComponentAvailability.CONSTRUCTION,
            message=message,
            icon_class=icon_class,
        )

    @property
    def has_overlay(self) -> bool:
        return (
            self.availability is ComponentAvailability.CONSTRUCTION
            or self.freshness is DataFreshness.STALE
        )

    @property
    def overlay_kind(self) -> str | None:
        if self.availability is ComponentAvailability.CONSTRUCTION:
            return ComponentAvailability.CONSTRUCTION.value
        if self.freshness is DataFreshness.STALE:
            return DataFreshness.STALE.value
        return None


def _require_class_tokens(value: str) -> None:
    tokens = value.split()
    if not tokens or not all(_CLASS_TOKEN.fullmatch(token) for token in tokens):
        raise StateWrapperDefinitionError(f'Invalid state wrapper CSS classes: {value!r}')
