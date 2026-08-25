# Declara puertos para Source, Publisher, Projection y catálogo de destinos.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
from collections.abc import Callable
from typing import Protocol

from ada.configuration.kpis.bundle import KpiConfigurationBundle
from ada.configuration.kpis.destinations import KpiDestinationCatalog
from ada.configuration.kpis.projection import KpiConfigurationProjection

KpiAuditActorProvider = Callable[[], str]


class KpiConfigurationSource(Protocol):
    def fetch_bundle(self) -> KpiConfigurationBundle | None: ...

    def list_history(self, *, limit: int = 20) -> tuple[KpiConfigurationBundle, ...]: ...

    def fetch_revision(self, revision: str) -> KpiConfigurationBundle | None: ...


class KpiConfigurationPublisher(Protocol):
    def publish_bundle(
        self,
        bundle: KpiConfigurationBundle,
        *,
        expected_source_revision: str | None,
    ) -> None: ...


class KpiProjectionRepository(Protocol):
    def load(self) -> KpiConfigurationProjection | None: ...

    def save(
        self,
        projection: KpiConfigurationProjection,
    ) -> KpiConfigurationProjection: ...

    def health_check(self) -> bool: ...


class KpiDestinationCatalogProvider(Protocol):
    def load(self) -> KpiDestinationCatalog | None: ...
