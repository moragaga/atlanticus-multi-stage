from datetime import UTC, datetime

from ada.configuration.kpis import KpiBinding, KpiConfiguration
from ada.configuration.kpis.adapters.cosmos import (
    CosmosKpiProjectionRepository,
    CosmosKpiProjectionSettings,
)
from ada.configuration.kpis.projection import KpiConfigurationProjection


class Client:
    def __init__(self) -> None:
        self.item = None

    def health_check(self) -> bool:
        return True

    def find_item(self, *, container_name, item_id, partition_key):
        assert container_name == 'configuration'
        assert item_id == 'kpis'
        assert partition_key == 'kpis'
        return self.item

    def upsert_item(self, *, container_name, item):
        assert container_name == 'configuration'
        self.item = item
        return item


def test_cosmos_projection_roundtrip() -> None:
    client = Client()
    repository = CosmosKpiProjectionRepository(
        client=client,
        settings=CosmosKpiProjectionSettings(container_name='configuration'),
    )
    projection = KpiConfigurationProjection.create(
        source_revision='source-r1',
        tool_projection_revision='tool-r1',
        projected_by='tester',
        projected_at_utc=datetime(2026, 8, 24, 20, 0, tzinfo=UTC),
        configuration=KpiConfiguration((KpiBinding(key='kpi_a', destination_keys=('molienda',)),)),
    )

    repository.save(projection)

    assert repository.load() == projection
    assert client.item['document_type'] == 'ada_kpi_configuration_projection'
    assert client.item['tool_projection_revision'] == 'tool-r1'
