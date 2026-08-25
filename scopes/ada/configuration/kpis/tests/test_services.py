from dataclasses import dataclass

import pytest

from ada.configuration.kpis import (
    KpiBinding,
    KpiConfiguration,
    KpiDestination,
    KpiDestinationCatalog,
    compose_kpi_configuration_services,
)
from ada.configuration.kpis.adapters.memory import (
    MemoryKpiConfigurationStore,
    MemoryKpiProjectionRepository,
)
from ada.configuration.kpis.errors import (
    KpiConfigurationProjectionError,
    KpiConfigurationValidationError,
)


@dataclass
class DestinationProvider:
    catalog: KpiDestinationCatalog | None

    def load(self) -> KpiDestinationCatalog | None:
        return self.catalog


def _provider(revision: str = 'tool-r1') -> DestinationProvider:
    return DestinationProvider(
        KpiDestinationCatalog(
            tool_projection_revision=revision,
            destinations=(
                KpiDestination('global_indicators', 'Indicadores Globales'),
                KpiDestination('time_status', 'Estado Temporal'),
                KpiDestination('molienda', 'Molienda'),
            ),
        )
    )


def _services(provider: DestinationProvider):
    source = MemoryKpiConfigurationStore()
    projection = MemoryKpiProjectionRepository()
    services = compose_kpi_configuration_services(
        source=source,
        publisher=source,
        projection=projection,
        destinations=provider,
        audit_actor_provider=lambda: 'tester',
    )
    return services, source, projection


def test_validation_accepts_multi_destination_and_disabled_kpis() -> None:
    services, _, _ = _services(_provider())
    configuration = KpiConfiguration(
        (
            KpiBinding(
                key='kpi_a',
                destination_keys=('global_indicators', 'molienda'),
                latest_enabled=False,
                series_enabled=False,
            ),
        )
    )

    result = services.administration.validate_configuration(configuration)

    assert result.valid
    assert result.tool_projection_revision == 'tool-r1'
    assert not result.issues


def test_validation_uses_only_stable_projected_destinations() -> None:
    services, _, _ = _services(_provider())
    configuration = KpiConfiguration(
        (KpiBinding(key='kpi_a', destination_keys=('draft_only_component',)),)
    )

    result = services.administration.validate_configuration(configuration)

    assert not result.valid
    assert result.issues[0].code == 'kpi.destination.unavailable'


def test_missing_tool_projection_makes_validation_invalid() -> None:
    services, _, _ = _services(DestinationProvider(None))
    configuration = KpiConfiguration((KpiBinding(key='kpi_a', destination_keys=('molienda',)),))

    result = services.administration.validate_configuration(configuration)

    assert not result.valid
    assert result.tool_projection_revision is None
    assert result.issues[0].code == 'kpi.tool_projection.missing'


def test_publish_and_project_record_tool_projection_revision() -> None:
    services, _, projection = _services(_provider('tool-r1'))
    configuration = KpiConfiguration(
        (
            KpiBinding(
                key='kpi_a',
                destination_keys=('molienda',),
                latest_enabled=True,
                series_enabled=True,
                series_hours=24,
            ),
        )
    )

    published = services.administration.publish_configuration(
        configuration,
        expected_source_revision=None,
    )
    result = services.projection_workflow.project(published.source_revision)
    active = projection.load()

    assert result.tool_projection_revision == 'tool-r1'
    assert active is not None
    assert active.tool_projection_revision == 'tool-r1'
    assert active.configuration == configuration


def test_projection_revalidates_against_current_tool_projection() -> None:
    provider = _provider('tool-r1')
    services, _, _ = _services(provider)
    configuration = KpiConfiguration((KpiBinding(key='kpi_a', destination_keys=('molienda',)),))
    published = services.administration.publish_configuration(
        configuration,
        expected_source_revision=None,
    )
    provider.catalog = KpiDestinationCatalog(
        tool_projection_revision='tool-r2',
        destinations=(KpiDestination('time_status', 'Estado Temporal'),),
    )

    with pytest.raises(KpiConfigurationProjectionError, match='not valid for projection'):
        services.projection_workflow.project(published.source_revision)


def test_publication_rejects_invalid_projected_destination() -> None:
    services, _, _ = _services(_provider())
    configuration = KpiConfiguration((KpiBinding(key='kpi_a', destination_keys=('unknown',)),))

    with pytest.raises(KpiConfigurationValidationError, match='must be valid'):
        services.administration.publish_configuration(
            configuration,
            expected_source_revision=None,
        )
