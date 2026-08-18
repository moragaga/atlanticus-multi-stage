# Espejo pedagógico: conserva la misma lógica del archivo productivo.
# Los comentarios documentan la responsabilidad sin cambiar el comportamiento.
# Define puertos independientes para fuente, publicación y proyección.
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
    def publish_bundle(self, bundle: ToolConfigurationBundle) -> None: ...


class ToolProjectionRepository(Protocol):
    def load(self) -> ToolConfigurationProjection | None: ...

    def save(
        self,
        projection: ToolConfigurationProjection,
    ) -> ToolConfigurationProjection: ...

    def health_check(self) -> bool: ...
