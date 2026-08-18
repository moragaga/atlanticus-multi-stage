# Espejo pedagógico: conserva la misma lógica del archivo productivo.
# Los comentarios documentan la responsabilidad sin cambiar el comportamiento.
# Persiste únicamente el ToolManifestRegistry activo para consumo runtime.
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ada.configuration.tools.errors import ToolConfigurationProjectionError
from ada.configuration.tools.projection import ToolConfigurationProjection


class CosmosClient(Protocol):
    def health_check(self) -> bool: ...

    def find_item(
        self,
        *,
        container_name: str,
        item_id: str,
        partition_key: object,
    ) -> dict[str, Any] | None: ...

    def upsert_item(
        self,
        *,
        container_name: str,
        item: dict[str, Any],
    ) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class CosmosToolProjectionSettings:
    container_name: str
    item_id: str = 'tools'
    partition_key: str = 'tools'

    def __post_init__(self) -> None:
        if not self.container_name.strip():
            raise ValueError('Cosmos tool configuration container must not be empty')


class CosmosToolProjectionRepository:
    def __init__(
        self,
        *,
        client: CosmosClient,
        settings: CosmosToolProjectionSettings,
    ) -> None:
        self._client = client
        self._settings = settings

    def load(self) -> ToolConfigurationProjection | None:
        try:
            document = self._client.find_item(
                container_name=self._settings.container_name,
                item_id=self._settings.item_id,
                partition_key=self._settings.partition_key,
            )
        except Exception as error:
            raise ToolConfigurationProjectionError(
                'Could not read Cosmos tool projection'
            ) from error
        if document is None:
            return None
        return ToolConfigurationProjection.from_document(document)

    def save(
        self,
        projection: ToolConfigurationProjection,
    ) -> ToolConfigurationProjection:
        try:
            self._client.upsert_item(
                container_name=self._settings.container_name,
                item=projection.to_document(
                    item_id=self._settings.item_id,
                    partition_key=self._settings.partition_key,
                ),
            )
        except Exception as error:
            raise ToolConfigurationProjectionError(
                'Could not write Cosmos tool projection'
            ) from error
        return projection

    def health_check(self) -> bool:
        try:
            return bool(self._client.health_check())
        except Exception:
            return False
