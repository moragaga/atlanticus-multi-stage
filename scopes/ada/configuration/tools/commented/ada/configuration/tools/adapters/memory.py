# Espejo pedagógico: conserva la misma lógica del archivo productivo.
# Los comentarios documentan la responsabilidad sin cambiar el comportamiento.
# Ofrece dobles en memoria para probar contratos sin infraestructura.
from __future__ import annotations

from dataclasses import dataclass

from ada.configuration.tools.bundle import (
    ToolConfigurationBundle,
    ToolConfigurationSourceDocument,
)
from ada.configuration.tools.projection import ToolConfigurationProjection


@dataclass(slots=True)
class MemoryToolConfigurationStore:
    source: ToolConfigurationSourceDocument | None = None

    def fetch_bundle(self) -> ToolConfigurationBundle | None:
        return self.source.current_bundle() if self.source is not None else None

    def publish_bundle(self, bundle: ToolConfigurationBundle) -> None:
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
