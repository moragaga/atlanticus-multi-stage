from datetime import UTC, datetime

from ada.configuration.kpis import KpiBinding, KpiConfiguration
from ada.configuration.kpis.adapters.file import (
    FileKpiConfigurationSettings,
    FileKpiConfigurationStore,
    FileKpiProjectionRepository,
    FileKpiProjectionSettings,
)
from ada.configuration.kpis.bundle import KpiConfigurationBundle
from ada.configuration.kpis.projection import KpiConfigurationProjection


def test_file_source_and_projection_roundtrip(tmp_path) -> None:
    configuration = KpiConfiguration((KpiBinding(key='kpi_a', destination_keys=('molienda',)),))
    bundle = KpiConfigurationBundle.create(
        configuration=configuration,
        saved_by='tester',
        now_utc=datetime(2026, 8, 24, 20, 0, tzinfo=UTC),
    )
    source = FileKpiConfigurationStore(FileKpiConfigurationSettings(root=tmp_path))
    source.publish_bundle(bundle, expected_source_revision=None)

    projection_value = KpiConfigurationProjection.create(
        source_revision=bundle.revision,
        tool_projection_revision='tool-r1',
        projected_by='tester',
        projected_at_utc=datetime(2026, 8, 24, 20, 1, tzinfo=UTC),
        configuration=configuration,
    )
    projection = FileKpiProjectionRepository(FileKpiProjectionSettings(root=tmp_path))
    projection.save(projection_value)

    assert source.fetch_bundle() == bundle
    assert source.fetch_revision(bundle.revision) == bundle
    assert projection.load() == projection_value
    assert (tmp_path / 'kpi_configuration.json.gz').exists()
    assert (tmp_path / 'kpis.json').exists()
