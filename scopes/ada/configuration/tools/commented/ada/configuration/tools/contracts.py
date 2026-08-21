# Declara los contratos de configuración de Tools; publicar exige la revisión de Source que el caller espera conservar.
# El contrato mantiene separados lectura, publicación e infraestructura concreta.

from collections.abc import Callable
from typing import Protocol

from ada.configuration.tools.bundle import ToolConfigurationBundle
from ada.configuration.tools.projection import ToolConfigurationProjection

ToolAuditActorProvider = Callable[[], str]


class ToolConfigurationSource(Protocol):
    def fetch_bundle(self) -> ToolConfigurationBundle | None: ...

    def list_history(self, *, limit: int = 20) -> tuple[ToolConfigurationBundle, ...]: ...

    def fetch_revision(self, revision: str) -> ToolConfigurationBundle | None: ...


class ToolConfigurationPublisher(Protocol):
    def publish_bundle(
        self,
        bundle: ToolConfigurationBundle,
        *,
        expected_source_revision: str | None,
    ) -> None: ...


class ToolProjectionRepository(Protocol):
    def load(self) -> ToolConfigurationProjection | None: ...

    def save(
        self,
        projection: ToolConfigurationProjection,
    ) -> ToolConfigurationProjection: ...

    def health_check(self) -> bool: ...
