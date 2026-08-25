# Proporciona almacenamiento en memoria para pruebas de Source/History y Projection.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
from __future__ import annotations

from ada.configuration.kpis.bundle import (
    KpiConfigurationBundle,
    KpiConfigurationSourceDocument,
)
from ada.configuration.kpis.errors import KpiConfigurationSourceError
from ada.configuration.kpis.projection import KpiConfigurationProjection


class MemoryKpiConfigurationStore:
    def __init__(self) -> None:
        self._source: KpiConfigurationSourceDocument | None = None

    def fetch_bundle(self) -> KpiConfigurationBundle | None:
        return self._source.current_bundle() if self._source is not None else None

    def publish_bundle(
        self,
        bundle: KpiConfigurationBundle,
        *,
        expected_source_revision: str | None,
    ) -> None:
        current_bundle = self.fetch_bundle()
        current_revision = current_bundle.revision if current_bundle is not None else None
        if current_revision != expected_source_revision:
            raise KpiConfigurationSourceError('KPI source revision changed before publication')
        self._source = (
            KpiConfigurationSourceDocument.from_bundle(bundle)
            if self._source is None
            else self._source.publish(bundle)
        )

    def list_history(self, *, limit: int = 20) -> tuple[KpiConfigurationBundle, ...]:
        return self._source.list_history(limit=limit) if self._source is not None else ()

    def fetch_revision(self, revision: str) -> KpiConfigurationBundle | None:
        return self._source.fetch_revision(revision) if self._source is not None else None


class MemoryKpiProjectionRepository:
    def __init__(self) -> None:
        self._projection: KpiConfigurationProjection | None = None

    def load(self) -> KpiConfigurationProjection | None:
        return self._projection

    def save(
        self,
        projection: KpiConfigurationProjection,
    ) -> KpiConfigurationProjection:
        self._projection = projection
        return projection

    def health_check(self) -> bool:
        return True
