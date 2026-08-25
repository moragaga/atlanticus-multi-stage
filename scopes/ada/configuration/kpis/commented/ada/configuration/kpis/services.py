# Compone validación/publicación/proyección sin leer directamente Tool Source o History.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from ada.configuration.kpis.bundle import KpiConfigurationBundle, build_kpi_configuration_digest
from ada.configuration.kpis.contracts import (
    KpiAuditActorProvider,
    KpiConfigurationPublisher,
    KpiConfigurationSource,
    KpiDestinationCatalogProvider,
    KpiProjectionRepository,
)
from ada.configuration.kpis.destinations import KpiDestinationCatalog
from ada.configuration.kpis.errors import (
    KpiConfigurationProjectionError,
    KpiConfigurationSourceError,
    KpiConfigurationValidationError,
)
from ada.configuration.kpis.models import KpiConfiguration
from ada.configuration.kpis.projection import (
    KpiConfigurationProjection,
    KpiDraftValidationResult,
    KpiProjectionAuditRecord,
    KpiProjectionExecutionResult,
    KpiProjectionIssue,
    KpiProjectionStatus,
    KpiProjectionSummaryItem,
    KpiSourcePublicationResult,
)


@dataclass(frozen=True, slots=True)
class KpiConfigurationServices:
    administration: KpiAdministrationService
    projection_workflow: KpiProjectionWorkflow
    projection: KpiProjectionRepository
    destinations: KpiDestinationCatalogProvider


class KpiAdministrationService:
    def __init__(
        self,
        *,
        source: KpiConfigurationSource,
        publisher: KpiConfigurationPublisher,
        destinations: KpiDestinationCatalogProvider,
        audit_actor_provider: KpiAuditActorProvider,
    ) -> None:
        self._source = source
        self._publisher = publisher
        self._destinations = destinations
        self._audit_actor_provider = audit_actor_provider

    def load_source(self) -> KpiConfigurationBundle | None:
        return self._source.fetch_bundle()

    def load_bundle(self) -> KpiConfigurationBundle:
        bundle = self.load_source()
        if bundle is None:
            raise KpiConfigurationSourceError('KPI configuration source does not exist')
        return bundle

    def load_configuration(self) -> KpiConfiguration:
        return self.load_bundle().configuration

    def validate_configuration(
        self,
        configuration: KpiConfiguration,
    ) -> KpiDraftValidationResult:
        actor = self._audit_actor_provider()
        occurred_at = datetime.now(UTC)
        catalog = self._destinations.load()
        issues = _validate_configuration(configuration, catalog)
        return KpiDraftValidationResult(
            draft_revision=build_kpi_configuration_digest(configuration),
            valid=not any(issue.level == 'error' for issue in issues),
            audit=KpiProjectionAuditRecord(actor=actor, occurred_at_utc=occurred_at),
            tool_projection_revision=(
                catalog.tool_projection_revision if catalog is not None else None
            ),
            issues=issues,
            summary=_configuration_summary(configuration),
        )

    def publish_configuration(
        self,
        configuration: KpiConfiguration,
        *,
        expected_source_revision: str | None,
    ) -> KpiSourcePublicationResult:
        current = self.load_source()
        current_revision = current.revision if current is not None else None
        if current_revision != expected_source_revision:
            raise KpiConfigurationValidationError(
                'KPI source revision changed before source publication'
            )
        validation = self.validate_configuration(configuration)
        if not validation.valid:
            raise KpiConfigurationValidationError(
                'KPI configuration must be valid before source publication'
            )
        actor = self._audit_actor_provider()
        occurred_at = datetime.now(UTC)
        bundle = KpiConfigurationBundle.create(
            configuration=configuration,
            saved_by=actor,
            now_utc=occurred_at,
        )
        published = current_revision != bundle.revision
        self._publisher.publish_bundle(
            bundle,
            expected_source_revision=expected_source_revision,
        )
        return KpiSourcePublicationResult(
            source_revision=bundle.revision,
            published=published,
            audit=KpiProjectionAuditRecord(actor=actor, occurred_at_utc=occurred_at),
            tool_projection_revision=validation.tool_projection_revision,
            summary=_configuration_summary(configuration),
        )

    def list_history(self, *, limit: int = 20) -> tuple[KpiConfigurationBundle, ...]:
        return self._source.list_history(limit=limit)

    def load_revision_configuration(self, revision: str) -> KpiConfiguration:
        bundle = self._source.fetch_revision(revision.strip())
        if bundle is None:
            raise KpiConfigurationSourceError('KPI configuration revision does not exist')
        return bundle.configuration


class KpiProjectionWorkflow:
    def __init__(
        self,
        *,
        source: KpiConfigurationSource,
        projection: KpiProjectionRepository,
        destinations: KpiDestinationCatalogProvider,
        audit_actor_provider: KpiAuditActorProvider,
    ) -> None:
        self._source = source
        self._projection = projection
        self._destinations = destinations
        self._audit_actor_provider = audit_actor_provider

    def get_status(self) -> KpiProjectionStatus:
        bundle = self._source.fetch_bundle()
        active = self._projection.load()
        return KpiProjectionStatus(
            source_revision=bundle.revision if bundle is not None else None,
            source_audit=(
                KpiProjectionAuditRecord(
                    actor=bundle.saved_by,
                    occurred_at_utc=bundle.saved_at_utc,
                )
                if bundle is not None
                else None
            ),
            active_revision=active.revision if active is not None else None,
            active_source_revision=active.source_revision if active is not None else None,
            active_tool_projection_revision=(
                active.tool_projection_revision if active is not None else None
            ),
            projection_audit=(
                KpiProjectionAuditRecord(
                    actor=active.projected_by,
                    occurred_at_utc=active.projected_at_utc,
                )
                if active is not None
                else None
            ),
        )

    def project(self, expected_source_revision: str) -> KpiProjectionExecutionResult:
        expected = expected_source_revision.strip()
        if not expected:
            raise KpiConfigurationProjectionError('Expected KPI source revision must not be empty')
        bundle = self._require_source_bundle(expected_revision=expected)
        catalog = self._require_destination_catalog()
        issues = _validate_configuration(bundle.configuration, catalog)
        if any(issue.level == 'error' for issue in issues):
            raise KpiConfigurationProjectionError(
                'Published KPI configuration is not valid for projection'
            )
        self._require_source_bundle(expected_revision=expected)
        self._require_destination_catalog(expected_revision=catalog.tool_projection_revision)
        actor = self._audit_actor_provider()
        occurred_at = datetime.now(UTC)
        projection = KpiConfigurationProjection.create(
            source_revision=bundle.revision,
            tool_projection_revision=catalog.tool_projection_revision,
            projected_by=actor,
            projected_at_utc=occurred_at,
            configuration=bundle.configuration,
        )
        self._require_source_bundle(expected_revision=expected)
        self._require_destination_catalog(expected_revision=catalog.tool_projection_revision)
        saved = self._projection.save(projection)
        return KpiProjectionExecutionResult(
            source_revision=bundle.revision,
            projection_revision=saved.revision,
            tool_projection_revision=catalog.tool_projection_revision,
            projected=True,
            audit=KpiProjectionAuditRecord(actor=actor, occurred_at_utc=occurred_at),
            summary=_configuration_summary(bundle.configuration),
        )

    def _require_source_bundle(
        self,
        *,
        expected_revision: str | None = None,
    ) -> KpiConfigurationBundle:
        bundle = self._source.fetch_bundle()
        if bundle is None:
            raise KpiConfigurationSourceError('KPI configuration source does not exist')
        if expected_revision is not None and bundle.revision != expected_revision:
            raise KpiConfigurationProjectionError('KPI source revision changed before projection')
        return bundle

    def _require_destination_catalog(
        self,
        *,
        expected_revision: str | None = None,
    ) -> KpiDestinationCatalog:
        catalog = self._destinations.load()
        if catalog is None:
            raise KpiConfigurationProjectionError('Tool projection is not available')
        if expected_revision is not None and catalog.tool_projection_revision != expected_revision:
            raise KpiConfigurationProjectionError(
                'Tool projection revision changed before KPI projection'
            )
        return catalog


def compose_kpi_configuration_services(
    *,
    source: KpiConfigurationSource,
    publisher: KpiConfigurationPublisher,
    projection: KpiProjectionRepository,
    destinations: KpiDestinationCatalogProvider,
    audit_actor_provider: KpiAuditActorProvider,
) -> KpiConfigurationServices:
    administration = KpiAdministrationService(
        source=source,
        publisher=publisher,
        destinations=destinations,
        audit_actor_provider=audit_actor_provider,
    )
    workflow = KpiProjectionWorkflow(
        source=source,
        projection=projection,
        destinations=destinations,
        audit_actor_provider=audit_actor_provider,
    )
    return KpiConfigurationServices(
        administration=administration,
        projection_workflow=workflow,
        projection=projection,
        destinations=destinations,
    )


def _validate_configuration(
    configuration: KpiConfiguration,
    catalog: KpiDestinationCatalog | None,
) -> tuple[KpiProjectionIssue, ...]:
    if catalog is None:
        return (
            KpiProjectionIssue(
                code='kpi.tool_projection.missing',
                message='Tool projection is not available',
                path='bindings',
            ),
        )
    available = catalog.keys
    issues: list[KpiProjectionIssue] = []
    for binding_index, binding in enumerate(configuration.bindings):
        for destination_index, destination_key in enumerate(binding.destination_keys):
            if destination_key not in available:
                issues.append(
                    KpiProjectionIssue(
                        code='kpi.destination.unavailable',
                        message=f'KPI destination {destination_key!r} is not available',
                        path=(f'bindings[{binding_index}].destination_keys[{destination_index}]'),
                    )
                )
    return tuple(issues)


def _configuration_summary(
    configuration: KpiConfiguration,
) -> tuple[KpiProjectionSummaryItem, ...]:
    active = sum(binding.enabled for binding in configuration.bindings)
    latest = sum(binding.latest_enabled for binding in configuration.bindings)
    series = sum(binding.series_enabled for binding in configuration.bindings)
    return (
        KpiProjectionSummaryItem('KPIs', str(len(configuration.bindings))),
        KpiProjectionSummaryItem('Activos', str(active)),
        KpiProjectionSummaryItem('Latest', str(latest)),
        KpiProjectionSummaryItem('Series', str(series)),
    )
