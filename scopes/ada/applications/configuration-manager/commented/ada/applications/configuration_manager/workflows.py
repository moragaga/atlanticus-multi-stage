from __future__ import annotations

from ada.configuration.tools import ToolConfigurationCatalog, ToolConfigurationServices
from atlanticus.web.manager import (
    DraftValidationResult,
    ProjectionAuditRecord,
    ProjectionExecutionResult,
    ProjectionIssue,
    ProjectionStatus,
    ProjectionSummaryItem,
    RevisionHistoryEntry,
    SourcePublicationResult,
)
from atlanticus.web.navigation.configuration import (
    NavigationConfigurationCatalog,
    NavigationConfigurationServices,
)
from atlanticus.web.users.configuration import (
    UsersConfigurationCatalog,
    UsersConfigurationServices,
)


# Define `ToolManagerWorkflowAdapter` como responsabilidad aislada dentro de Atlanticus.
class ToolManagerWorkflowAdapter:
    # Resuelve `init` manteniendo validación y estado explícitos.
    def __init__(self, services: ToolConfigurationServices) -> None:
        self._services = services
        self._workflow = services.projection_workflow
        self._administration = services.administration

    # Resuelve `get status` manteniendo validación y estado explícitos.
    def get_status(self) -> ProjectionStatus:
        status = self._workflow.get_status()
        return _status(status)

    # Resuelve `validate draft` manteniendo validación y estado explícitos.
    def validate_draft(self, payload: dict[str, object]) -> DraftValidationResult:
        catalog = ToolConfigurationCatalog.from_document(payload)
        result = self._administration.validate_catalog(catalog)
        return _validation(result)

    # Resuelve `publish draft` manteniendo validación y estado explícitos.
    def publish_draft(
        self,
        payload: dict[str, object],
        expected_source_revision: str | None,
    ) -> SourcePublicationResult:
        catalog = ToolConfigurationCatalog.from_document(payload)
        result = self._administration.publish_catalog(
            catalog,
            expected_source_revision=expected_source_revision,
        )
        return _publication(result)

    # Resuelve `project` manteniendo validación y estado explícitos.
    def project(self, expected_source_revision: str) -> ProjectionExecutionResult:
        return _projection(self._workflow.project(expected_source_revision))

    # Resuelve `load revision` manteniendo validación y estado explícitos.
    def load_revision(self, revision: str) -> dict[str, object]:
        return self._administration.load_revision_catalog(revision).to_document()

    # Resuelve `list history` manteniendo validación y estado explícitos.
    def list_history(self, *, limit: int = 20) -> tuple[RevisionHistoryEntry, ...]:
        status = self._workflow.get_status()
        return tuple(
            RevisionHistoryEntry(
                revision=bundle.revision,
                saved_by=bundle.saved_by,
                saved_at=bundle.saved_at_utc,
                active=bundle.revision == status.active_source_revision,
                current=bundle.revision == status.source_revision,
            )
            for bundle in self._administration.list_history(limit=limit)
        )


# Define `NavigationManagerWorkflowAdapter` como responsabilidad aislada dentro de Atlanticus.
class NavigationManagerWorkflowAdapter:
    # Resuelve `init` manteniendo validación y estado explícitos.
    def __init__(self, services: NavigationConfigurationServices) -> None:
        self._workflow = services.projection_workflow
        self._administration = services.administration

    # Resuelve `get status` manteniendo validación y estado explícitos.
    def get_status(self) -> ProjectionStatus:
        return _status(self._workflow.get_status())

    # Resuelve `validate draft` manteniendo validación y estado explícitos.
    def validate_draft(self, payload: dict[str, object]) -> DraftValidationResult:
        catalog = NavigationConfigurationCatalog.from_document(payload)
        return _validation(self._administration.validate_catalog(catalog))

    # Resuelve `publish draft` manteniendo validación y estado explícitos.
    def publish_draft(
        self,
        payload: dict[str, object],
        expected_source_revision: str | None,
    ) -> SourcePublicationResult:
        catalog = NavigationConfigurationCatalog.from_document(payload)
        result = self._administration.publish_catalog(
            catalog,
            expected_source_revision=expected_source_revision,
        )
        return _publication(result)

    # Resuelve `project` manteniendo validación y estado explícitos.
    def project(self, expected_source_revision: str) -> ProjectionExecutionResult:
        return _projection(self._workflow.project(expected_source_revision))

    # Resuelve `load revision` manteniendo validación y estado explícitos.
    def load_revision(self, revision: str) -> dict[str, object]:
        return self._administration.load_revision_catalog(revision).to_document()

    # Resuelve `list history` manteniendo validación y estado explícitos.
    def list_history(self, *, limit: int = 20) -> tuple[RevisionHistoryEntry, ...]:
        status = self._workflow.get_status()
        return tuple(
            RevisionHistoryEntry(
                revision=bundle.revision,
                saved_by=bundle.saved_by,
                saved_at=bundle.saved_at_utc,
                active=bundle.revision == status.active_source_revision,
                current=bundle.revision == status.source_revision,
            )
            for bundle in self._administration.list_history(limit=limit)
        )


# Define `UsersManagerWorkflowAdapter` como responsabilidad aislada dentro de Atlanticus.
class UsersManagerWorkflowAdapter:
    # Resuelve `init` manteniendo validación y estado explícitos.
    def __init__(self, services: UsersConfigurationServices) -> None:
        self._services = services
        self._workflow = services.projection_workflow
        self._administration = services.administration

    # Resuelve `get status` manteniendo validación y estado explícitos.
    def get_status(self) -> ProjectionStatus:
        return _status(self._workflow.get_status())

    # Resuelve `validate draft` manteniendo validación y estado explícitos.
    def validate_draft(self, payload: dict[str, object]) -> DraftValidationResult:
        catalog = UsersConfigurationCatalog.from_document(payload)
        return _validation(self._administration.validate_catalog(catalog))

    # Resuelve `publish draft` manteniendo validación y estado explícitos.
    def publish_draft(
        self,
        payload: dict[str, object],
        expected_source_revision: str | None,
    ) -> SourcePublicationResult:
        catalog = UsersConfigurationCatalog.from_document(payload)
        result = self._administration.publish_catalog(
            catalog,
            expected_source_revision=expected_source_revision,
        )
        return _publication(result)

    # Resuelve `project` manteniendo validación y estado explícitos.
    def project(self, expected_source_revision: str) -> ProjectionExecutionResult:
        return _projection(self._workflow.project(expected_source_revision))

    # Resuelve `load revision` manteniendo validación y estado explícitos.
    def load_revision(self, revision: str) -> dict[str, object]:
        return self._administration.load_revision_catalog(revision).to_document()

    # Resuelve `list history` manteniendo validación y estado explícitos.
    def list_history(self, *, limit: int = 20) -> tuple[RevisionHistoryEntry, ...]:
        status = self._workflow.get_status()
        return tuple(
            RevisionHistoryEntry(
                revision=bundle.revision,
                saved_by=bundle.saved_by,
                saved_at=bundle.saved_at_utc,
                active=bundle.revision == status.active_source_revision,
                current=bundle.revision == status.source_revision,
            )
            for bundle in self._administration.list_history(limit=limit)
        )


# Resuelve `status` manteniendo validación y estado explícitos.
def _status(status) -> ProjectionStatus:
    return ProjectionStatus(
        source_revision=status.source_revision,
        source_audit=_optional_audit(status.source_audit),
        active_revision=status.active_revision,
        active_source_revision=status.active_source_revision,
        projection_audit=_optional_audit(status.projection_audit),
    )


# Resuelve `validation` manteniendo validación y estado explícitos.
def _validation(result) -> DraftValidationResult:
    return DraftValidationResult(
        draft_revision=result.draft_revision,
        valid=result.valid,
        audit=_audit(result.audit),
        issues=tuple(_issue(issue) for issue in result.issues),
        summary=tuple(_summary(item) for item in result.summary),
    )


# Resuelve `publication` manteniendo validación y estado explícitos.
def _publication(result) -> SourcePublicationResult:
    return SourcePublicationResult(
        source_revision=result.source_revision,
        published=result.published,
        audit=_audit(result.audit),
        summary=tuple(_summary(item) for item in result.summary),
    )


# Resuelve `projection` manteniendo validación y estado explícitos.
def _projection(result) -> ProjectionExecutionResult:
    return ProjectionExecutionResult(
        source_revision=result.source_revision,
        projection_revision=result.projection_revision,
        projected=result.projected,
        audit=_audit(result.audit),
        issues=tuple(_issue(issue) for issue in result.issues),
        summary=tuple(_summary(item) for item in result.summary),
    )


# Resuelve `optional audit` manteniendo validación y estado explícitos.
def _optional_audit(record) -> ProjectionAuditRecord | None:
    return _audit(record) if record is not None else None


# Resuelve `audit` manteniendo validación y estado explícitos.
def _audit(record) -> ProjectionAuditRecord:
    return ProjectionAuditRecord(
        actor=record.actor,
        occurred_at=record.occurred_at_utc,
    )


# Resuelve `issue` manteniendo validación y estado explícitos.
def _issue(issue) -> ProjectionIssue:
    return ProjectionIssue(
        code=issue.code,
        message=issue.message,
        level=issue.level,
        path=issue.path,
    )


# Resuelve `summary` manteniendo validación y estado explícitos.
def _summary(item) -> ProjectionSummaryItem:
    return ProjectionSummaryItem(label=item.label, value=item.value)
