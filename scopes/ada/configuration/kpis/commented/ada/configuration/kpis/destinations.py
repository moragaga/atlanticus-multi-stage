# Representa la vista estable y mínima de destinos que KPI recibe desde Tool Projection.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
from __future__ import annotations

from dataclasses import dataclass

from ada.configuration.kpis.errors import KpiConfigurationProjectionError
from ada.configuration.kpis.identity import require_identity_key


@dataclass(frozen=True, slots=True)
class KpiDestination:
    key: str
    display_name: str

    def __post_init__(self) -> None:
        key = require_identity_key(self.key, label='KPI destination key')
        display_name = self.display_name.strip()
        if not display_name:
            raise KpiConfigurationProjectionError('KPI destination display name must not be empty')
        object.__setattr__(self, 'key', key)
        object.__setattr__(self, 'display_name', display_name)


@dataclass(frozen=True, slots=True)
class KpiDestinationCatalog:
    tool_projection_revision: str
    destinations: tuple[KpiDestination, ...]

    def __post_init__(self) -> None:
        revision = self.tool_projection_revision.strip()
        destinations = tuple(self.destinations)
        if not revision:
            raise KpiConfigurationProjectionError('Tool projection revision must not be empty')
        keys = tuple(destination.key for destination in destinations)
        if len(keys) != len(set(keys)):
            raise KpiConfigurationProjectionError('KPI destination keys must be unique')
        object.__setattr__(self, 'tool_projection_revision', revision)
        object.__setattr__(self, 'destinations', destinations)

    @property
    def keys(self) -> frozenset[str]:
        return frozenset(destination.key for destination in self.destinations)

    def destination(self, key: str) -> KpiDestination | None:
        normalized = require_identity_key(key, label='KPI destination key')
        return next(
            (destination for destination in self.destinations if destination.key == normalized),
            None,
        )
