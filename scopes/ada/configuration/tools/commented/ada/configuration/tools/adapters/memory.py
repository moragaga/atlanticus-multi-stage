# Implementa el History en memoria de Tools usado por pruebas y respeta expected_source_revision antes de mutar estado.
# Esto permite probar la concurrencia del servicio sin depender de infraestructura externa.

from __future__ import annotations

from dataclasses import dataclass

from ada.configuration.tools.bundle import (
    ToolConfigurationBundle,
    ToolConfigurationSourceDocument,
)
from ada.configuration.tools.errors import ToolConfigurationSourceError
from ada.configuration.tools.projection import ToolConfigurationProjection


@dataclass(slots=True)
class MemoryToolConfigurationStore:
    source: ToolConfigurationSourceDocument | None = None

    def fetch_bundle(self) -> ToolConfigurationBundle | None:
        return self.source.current_bundle() if self.source is not None else None

    def publish_bundle(
        self,
        bundle: ToolConfigurationBundle,
        *,
        expected_source_revision: str | None,
    ) -> None:
        current = self.fetch_bundle()
        current_revision = current.revision if current is not None else None
        if current_revision != expected_source_revision:
            raise ToolConfigurationSourceError('Tool source revision changed before publication')
        if self.source is None:
            self.source = ToolConfigurationSourceDocument.from_bundle(bundle)
            return
        self.source = self.source.publish(bundle)

    def list_history(self, *, limit: int = 20) -> tuple[ToolConfigurationBundle, ...]:
        return self.source.list_history(limit=limit) if self.source is not None else ()

    def fetch_revision(self, revision: str) -> ToolConfigurationBundle | None:
        return self.source.fetch_revision(revision) if self.source is not None else None


@dataclass(slots=True)
class MemoryToolProjectionRepository:
    active: ToolConfigurationProjection | None = None

    def load(self) -> ToolConfigurationProjection | None:
        return self.active

    def save(
        self,
        projection: ToolConfigurationProjection,
    ) -> ToolConfigurationProjection:
        self.active = projection
        return projection

    def health_check(self) -> bool:
        return True
