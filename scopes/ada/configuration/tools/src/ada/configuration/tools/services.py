from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from ada.configuration.tools.builder import build_tool_manifest
from ada.configuration.tools.bundle import (
    ToolConfigurationBundle,
    build_tool_configuration_digest,
)
from ada.configuration.tools.contracts import (
    ToolAuditActorProvider,
    ToolConfigurationPublisher,
    ToolConfigurationSource,
    ToolProjectionRepository,
)
from ada.configuration.tools.errors import (
    ToolConfigurationProjectionError,
    ToolConfigurationSourceError,
    ToolConfigurationValidationError,
)
from ada.configuration.tools.models import ToolConfiguration
from ada.configuration.tools.projection import (
    ToolConfigurationProjection,
    ToolDraftValidationResult,
    ToolProjectionAuditRecord,
    ToolProjectionExecutionResult,
    ToolProjectionIssue,
    ToolProjectionStatus,
    ToolProjectionSummaryItem,
    ToolSourcePublicationResult,
)


@dataclass(frozen=True, slots=True)
class ToolConfigurationServices:
    administration: ToolAdministrationService
    projection_workflow: ToolProjectionWorkflow
    projection: ToolProjectionRepository


class ToolAdministrationService:
    def __init__(
        self,
        *,
        source: ToolConfigurationSource,
        publisher: ToolConfigurationPublisher,
        audit_actor_provider: ToolAuditActorProvider,
    ) -> None:
        self._source = source
        self._publisher = publisher
        self._audit_actor_provider = audit_actor_provider

    def load_source(self) -> ToolConfigurationBundle | None:
        return self._source.fetch_bundle()

    def load_bundle(self) -> ToolConfigurationBundle:
        bundle = self.load_source()
        if bundle is None:
            raise ToolConfigurationSourceError('Tool configuration source does not exist')
        return bundle

    def load_configuration(self) -> ToolConfiguration:
        return self.load_bundle().configuration

    def validate_configuration(
        self,
        configuration: ToolConfiguration,
    ) -> ToolDraftValidationResult:
        actor = self._audit_actor_provider()
        occurred_at = datetime.now(UTC)
        issues = _validate_configuration(configuration)
        return ToolDraftValidationResult(
            draft_revision=build_tool_configuration_digest(configuration),
            valid=not any(issue.level == 'error' for issue in issues),
            audit=ToolProjectionAuditRecord(actor=actor, occurred_at_utc=occurred_at),
            issues=issues,
            summary=_configuration_summary(configuration),
        )

    def publish_configuration(
        self,
        configuration: ToolConfiguration,
        *,
        expected_source_revision: str | None,
    ) -> ToolSourcePublicationResult:
        current = self.load_source()
        current_revision = current.revision if current is not None else None
        if current_revision != expected_source_revision:
            raise ToolConfigurationValidationError(
                'Tool source revision changed before source publication'
            )
        validation = self.validate_configuration(configuration)
        if not validation.valid:
            raise ToolConfigurationValidationError(
                'Tool configuration must be valid before source publication'
            )
        actor = self._audit_actor_provider()
        occurred_at = datetime.now(UTC)
        bundle = ToolConfigurationBundle.create(
            configuration=configuration,
            saved_by=actor,
            now_utc=occurred_at,
        )
        published = current_revision != bundle.revision
        self._publisher.publish_bundle(
            bundle,
            expected_source_revision=expected_source_revision,
        )
        return ToolSourcePublicationResult(
            source_revision=bundle.revision,
            published=published,
            audit=ToolProjectionAuditRecord(actor=actor, occurred_at_utc=occurred_at),
            summary=_configuration_summary(configuration),
        )

    def list_history(self, *, limit: int = 20) -> tuple[ToolConfigurationBundle, ...]:
        return self._source.list_history(limit=limit)

    def load_revision_configuration(self, revision: str) -> ToolConfiguration:
        bundle = self._source.fetch_revision(revision.strip())
        if bundle is None:
            raise ToolConfigurationSourceError('Tool configuration revision does not exist')
        return bundle.configuration


class ToolProjectionWorkflow:
    def __init__(
        self,
        *,
        source: ToolConfigurationSource,
        projection: ToolProjectionRepository,
        audit_actor_provider: ToolAuditActorProvider,
    ) -> None:
        self._source = source
        self._projection = projection
        self._audit_actor_provider = audit_actor_provider

    def get_status(self) -> ToolProjectionStatus:
        bundle = self._source.fetch_bundle()
        active = self._projection.load()
        return ToolProjectionStatus(
            source_revision=bundle.revision if bundle is not None else None,
            source_audit=(
                ToolProjectionAuditRecord(
                    actor=bundle.saved_by,
                    occurred_at_utc=bundle.saved_at_utc,
                )
                if bundle is not None
                else None
            ),
            active_revision=active.revision if active is not None else None,
            active_source_revision=active.source_revision if active is not None else None,
            projection_audit=(
                ToolProjectionAuditRecord(
                    actor=active.projected_by,
                    occurred_at_utc=active.projected_at_utc,
                )
                if active is not None
                else None
            ),
        )

    def project(self, expected_source_revision: str) -> ToolProjectionExecutionResult:
        expected = expected_source_revision.strip()
        if not expected:
            raise ToolConfigurationProjectionError(
                'Expected tool source revision must not be empty'
            )
        bundle = self._require_source_bundle(expected_revision=expected)
        issues = _validate_configuration(bundle.configuration)
        if any(issue.level == 'error' for issue in issues):
            raise ToolConfigurationProjectionError(
                'Published tool configuration is not valid for projection'
            )
        manifest = build_tool_manifest(bundle.configuration)
        self._require_source_bundle(expected_revision=expected)
        actor = self._audit_actor_provider()
        occurred_at = datetime.now(UTC)
        projection = ToolConfigurationProjection.create(
            source_revision=bundle.revision,
            projected_by=actor,
            projected_at_utc=occurred_at,
            manifest=manifest,
        )
        self._require_source_bundle(expected_revision=expected)
        saved = self._projection.save(projection)
        return ToolProjectionExecutionResult(
            source_revision=bundle.revision,
            projection_revision=saved.revision,
            projected=True,
            audit=ToolProjectionAuditRecord(actor=actor, occurred_at_utc=occurred_at),
            summary=_configuration_summary(bundle.configuration),
        )

    def _require_source_bundle(
        self,
        *,
        expected_revision: str | None = None,
    ) -> ToolConfigurationBundle:
        bundle = self._source.fetch_bundle()
        if bundle is None:
            raise ToolConfigurationSourceError('Tool configuration source does not exist')
        if expected_revision is not None and bundle.revision != expected_revision:
            raise ToolConfigurationProjectionError('Tool source revision changed before projection')
        return bundle


def compose_tool_configuration_services(
    *,
    source: ToolConfigurationSource,
    publisher: ToolConfigurationPublisher,
    projection: ToolProjectionRepository,
    audit_actor_provider: ToolAuditActorProvider,
) -> ToolConfigurationServices:
    administration = ToolAdministrationService(
        source=source,
        publisher=publisher,
        audit_actor_provider=audit_actor_provider,
    )
    workflow = ToolProjectionWorkflow(
        source=source,
        projection=projection,
        audit_actor_provider=audit_actor_provider,
    )
    return ToolConfigurationServices(
        administration=administration,
        projection_workflow=workflow,
        projection=projection,
    )


def _validate_configuration(
    configuration: ToolConfiguration,
) -> tuple[ToolProjectionIssue, ...]:
    try:
        build_tool_manifest(configuration)
    except ToolConfigurationValidationError as error:
        return (
            ToolProjectionIssue(
                code='tool.invalid',
                message=str(error),
                path='tool',
            ),
        )
    return ()


def _configuration_summary(
    configuration: ToolConfiguration,
) -> tuple[ToolProjectionSummaryItem, ...]:
    components = len(configuration.components)
    subcomponents = sum(len(component.subcomponents) for component in configuration.components)
    return (
        ToolProjectionSummaryItem('Herramienta', configuration.display_name),
        ToolProjectionSummaryItem('Componentes', str(components)),
        ToolProjectionSummaryItem('Subcomponentes', str(subcomponents)),
    )
