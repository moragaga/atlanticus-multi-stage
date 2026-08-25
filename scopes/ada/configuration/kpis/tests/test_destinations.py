from datetime import UTC, datetime

from ada.configuration.kpis.adapters.tool_projection import ToolProjectionKpiDestinationProvider
from ada.configuration.tools.projection import ToolConfigurationProjection
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST


class Repository:
    def __init__(self) -> None:
        self.projection = None

    def load(self):
        return self.projection


def test_tool_projection_provider_exposes_only_kpi_components() -> None:
    repository = Repository()
    projection = ToolConfigurationProjection.create(
        source_revision='source-revision',
        projected_by='tester',
        projected_at_utc=datetime(2026, 8, 24, 20, 0, tzinfo=UTC),
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
    )
    repository.projection = projection

    catalog = ToolProjectionKpiDestinationProvider(repository).load()

    assert catalog is not None
    assert catalog.tool_projection_revision == projection.revision
    assert catalog.keys == {
        'global_indicators',
        'time_status',
        'general_mina',
        'carguio',
        'transporte',
        'chancado_stmg',
        'stockpile_chacay',
        'molienda',
        'flotacion',
        'transporte_fluidos',
        'puerto',
    }
    assert 'global_indicators_mine' not in catalog.keys
    assert 'global_indicators_plant' not in catalog.keys
    assert 'flotacion_selectiva' not in catalog.keys


def test_tool_projection_provider_returns_none_without_stable_projection() -> None:
    repository = Repository()

    assert ToolProjectionKpiDestinationProvider(repository).load() is None
