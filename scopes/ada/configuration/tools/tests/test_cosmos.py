from datetime import UTC, datetime

from ada.configuration.tools import (
    ToolConfigurationCatalog,
    ToolConfigurationProjection,
    build_tool_manifest_registry,
    integrated_operations_configuration_from_manifest,
)
from ada.configuration.tools.adapters.cosmos import (
    CosmosToolProjectionRepository,
    CosmosToolProjectionSettings,
)
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST


class FakeCosmosClient:
    def __init__(self) -> None:
        self.items: dict[str, dict[str, object]] = {}

    def health_check(self) -> bool:
        return True

    def find_item(self, *, container_name: str, item_id: str, partition_key: object):
        return self.items.get(item_id)

    def upsert_item(self, *, container_name: str, item: dict[str, object]):
        self.items[str(item['id'])] = dict(item)
        return item


def test_cosmos_repository_roundtrips_only_active_runtime_projection() -> None:
    client = FakeCosmosClient()
    repository = CosmosToolProjectionRepository(
        client=client,
        settings=CosmosToolProjectionSettings(container_name='configuration'),
    )
    registry = build_tool_manifest_registry(
        ToolConfigurationCatalog(
            (
                integrated_operations_configuration_from_manifest(
                    INTEGRATED_OPERATIONS_MANIFEST
                ),
            )
        )
    )
    projection = ToolConfigurationProjection.create(
        source_revision='source-revision',
        projected_by='Admin',
        projected_at_utc=datetime(2026, 8, 18, 12, 0, tzinfo=UTC),
        registry=registry,
    )

    repository.save(projection)

    assert repository.load() == projection
    assert repository.health_check()
    assert set(client.items) == {'tools'}
