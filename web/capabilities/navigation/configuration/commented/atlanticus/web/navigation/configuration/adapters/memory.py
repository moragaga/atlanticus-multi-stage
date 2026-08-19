# Espejo pedagógico: adapters en memoria para pruebas aisladas del workflow.
from __future__ import annotations

from dataclasses import dataclass

from atlanticus.web.navigation.configuration.bundle import (
    NavigationConfigurationBundle,
    NavigationConfigurationSourceDocument,
)
from atlanticus.web.navigation.configuration.projection import NavigationConfigurationProjection


@dataclass(slots=True)
class MemoryNavigationConfigurationStore:
    source: NavigationConfigurationSourceDocument | None = None

    def fetch_bundle(self) -> NavigationConfigurationBundle | None:
        return self.source.current_bundle() if self.source is not None else None

    def publish_bundle(self, bundle: NavigationConfigurationBundle) -> None:
        if self.source is None:
            self.source = NavigationConfigurationSourceDocument.from_bundle(bundle)
            return
        self.source = self.source.publish(bundle)

    def list_history(self, *, limit: int = 20) -> tuple[NavigationConfigurationBundle, ...]:
        return self.source.list_history(limit=limit) if self.source is not None else ()

    def fetch_revision(self, revision: str) -> NavigationConfigurationBundle | None:
        return self.source.fetch_revision(revision) if self.source is not None else None


@dataclass(slots=True)
class MemoryNavigationProjectionRepository:
    projection: NavigationConfigurationProjection | None = None

    def load(self) -> NavigationConfigurationProjection | None:
        return self.projection

    def save(
        self,
        projection: NavigationConfigurationProjection,
    ) -> NavigationConfigurationProjection:
        self.projection = projection
        return projection

    def health_check(self) -> bool:
        return True
