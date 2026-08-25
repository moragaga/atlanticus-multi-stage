# Implementa KPI Projection en Cosmos con documento independiente.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ada.configuration.kpis.errors import KpiConfigurationProjectionError
from ada.configuration.kpis.projection import KpiConfigurationProjection


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
class CosmosKpiProjectionSettings:
    container_name: str
    item_id: str = 'kpis'
    partition_key: str = 'kpis'

    def __post_init__(self) -> None:
        if not self.container_name.strip():
            raise ValueError('Cosmos KPI configuration container must not be empty')


class CosmosKpiProjectionRepository:
    def __init__(
        self,
        *,
        client: CosmosClient,
        settings: CosmosKpiProjectionSettings,
    ) -> None:
        self._client = client
        self._settings = settings

    def load(self) -> KpiConfigurationProjection | None:
        try:
            document = self._client.find_item(
                container_name=self._settings.container_name,
                item_id=self._settings.item_id,
                partition_key=self._settings.partition_key,
            )
        except Exception as error:
            raise KpiConfigurationProjectionError('Could not read Cosmos KPI projection') from error
        if document is None:
            return None
        return KpiConfigurationProjection.from_document(document)

    def save(
        self,
        projection: KpiConfigurationProjection,
    ) -> KpiConfigurationProjection:
        try:
            self._client.upsert_item(
                container_name=self._settings.container_name,
                item=projection.to_document(
                    item_id=self._settings.item_id,
                    partition_key=self._settings.partition_key,
                ),
            )
        except Exception as error:
            raise KpiConfigurationProjectionError(
                'Could not write Cosmos KPI projection'
            ) from error
        return projection

    def health_check(self) -> bool:
        try:
            return bool(self._client.health_check())
        except Exception:
            return False
