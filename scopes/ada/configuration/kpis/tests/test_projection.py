from datetime import UTC, datetime

from ada.configuration.kpis import KpiBinding, KpiConfiguration
from ada.configuration.kpis.projection import KpiConfigurationProjection


def test_projection_roundtrip_captures_tool_projection_revision() -> None:
    configuration = KpiConfiguration((KpiBinding(key='kpi_a', destination_keys=('molienda',)),))
    projection = KpiConfigurationProjection.create(
        source_revision='kpi-source',
        tool_projection_revision='tool-stable',
        projected_by='tester',
        projected_at_utc=datetime(2026, 8, 24, 20, 0, tzinfo=UTC),
        configuration=configuration,
    )

    document = projection.to_document(item_id='kpis', partition_key='kpis')

    assert document['tool_projection_revision'] == 'tool-stable'
    assert KpiConfigurationProjection.from_document(document) == projection
    assert 'tool_key' not in document['configuration']
