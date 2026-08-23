# Estos adapters convierten la Source tipada de cada módulo al snapshot genérico de importación, sin publicar ni proyectar.
from __future__ import annotations

from ada.configuration.tools import ToolConfigurationCatalog, ToolConfigurationServices
from ada.configuration.tools.contracts import ToolConfigurationSource
from atlanticus.web.manager import (
    DraftValidationResult,
    ProjectionAuditRecord,
    ProjectionExecutionResult,
    ProjectionIssue,
    ProjectionStatus,
    ProjectionSummaryItem,
    RevisionHistoryEntry,
    SourcePublicationResult,
    WorkspaceImportSnapshot,
)
from atlanticus.web.navigation.configuration import (
    NavigationConfigurationCatalog,
    NavigationConfigurationServices,
    NavigationConfigurationSource,
)
from atlanticus.web.users.configuration import (
    UsersConfigurationCatalog,
    UsersConfigurationServices,
    UsersConfigurationSource,
)


class ToolWorkspaceImportAdapter:
    def __init__(self, source: ToolConfigurationSource) -> None:
        self._source = source

    def load_current(self) -> WorkspaceImportSnapshot | None:
        bundle = self._source.fetch_bundle()
        if bundle is None:
            return None
        return WorkspaceImportSnapshot(
            revision=bundle.revision,
            payload=bundle.catalog.to_document(),
        )


class UsersWorkspaceImportAdapter:
    def __init__(self, source: UsersConfigurationSource) -> None:
        self._source = source

    def load_current(self) -> WorkspaceImportSnapshot | None:
        bundle = self._source.fetch_bundle()
        if bundle is None:
            return None
        return WorkspaceImportSnapshot(
            revision=bundle.revision,
            payload=bundle.catalog.to_document(),
        )


class NavigationWorkspaceImportAdapter:
    def __init__(self, source: NavigationConfigurationSource) -> None:
        self._source = source

    def load_current(self) -> WorkspaceImportSnapshot | None:
        bundle = self._source.fetch_bundle()
        if bundle is None:
            return None
        return WorkspaceImportSnapshot(
            revision=bundle.revision,
            payload=bundle.catalog.to_document(),
        )


class ToolManagerWorkflowAdapter:
    def __init__(self, services: ToolConfigurationServices) -> None:
        self._services = services
        self._workflow = services.projection_workflow
        self._administration = services.administration

    def get_status(self) -> ProjectionStatus:
        status = self._workflow.get_status()
        return _status(status)

    def validate_draft(self, payload: dict[str, object]) -> DraftValidationResult:
        catalog = ToolConfigurationCatalog.from_document(payload)
        result = self._administration.validate_catalog(catalog)
        return _validation(result)

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

    def project(self, expected_source_revision: str) -> ProjectionExecutionResult:
        return _projection(self._workflow.project(expected_source_revision))

    def load_revision(self, revision: str) -> dict[str, object]:
        return self._administration.load_revision_catalog(revision).to_document()

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


class NavigationManagerWorkflowAdapter:
    def __init__(self, services: NavigationConfigurationServices) -> None:
        self._workflow = services.projection_workflow
        self._administration = services.administration

    def get_status(self) -> ProjectionStatus:
        return _status(self._workflow.get_status())

    def validate_draft(self, payload: dict[str, object]) -> DraftValidationResult:
        catalog = NavigationConfigurationCatalog.from_document(payload)
        return _validation(self._administration.validate_catalog(catalog))

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

    def project(self, expected_source_revision: str) -> ProjectionExecutionResult:
        return _projection(self._workflow.project(expected_source_revision))

    def load_revision(self, revision: str) -> dict[str, object]:
        return self._administration.load_revision_catalog(revision).to_document()

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


class UsersManagerWorkflowAdapter:
    def __init__(self, services: UsersConfigurationServices) -> None:
        self._services = services
        self._workflow = services.projection_workflow
        self._administration = services.administration

    def get_status(self) -> ProjectionStatus:
        return _status(self._workflow.get_status())

    def validate_draft(self, payload: dict[str, object]) -> DraftValidationResult:
        catalog = UsersConfigurationCatalog.from_document(payload)
        return _validation(self._administration.validate_catalog(catalog))

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

    def project(self, expected_source_revision: str) -> ProjectionExecutionResult:
        return _projection(self._workflow.project(expected_source_revision))

    def load_revision(self, revision: str) -> dict[str, object]:
        return self._administration.load_revision_catalog(revision).to_document()

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


def _status(status) -> ProjectionStatus:
    return ProjectionStatus(
        source_revision=status.source_revision,
        source_audit=_optional_audit(status.source_audit),
        active_revision=status.active_revision,
        active_source_revision=status.active_source_revision,
        projection_audit=_optional_audit(status.projection_audit),
    )


def _validation(result) -> DraftValidationResult:
    return DraftValidationResult(
        draft_revision=result.draft_revision,
        valid=result.valid,
        audit=_audit(result.audit),
        issues=tuple(_issue(issue) for issue in result.issues),
        summary=tuple(_summary(item) for item in result.summary),
    )


def _publication(result) -> SourcePublicationResult:
    return SourcePublicationResult(
        source_revision=result.source_revision,
        published=result.published,
        audit=_audit(result.audit),
        summary=tuple(_summary(item) for item in result.summary),
    )


def _projection(result) -> ProjectionExecutionResult:
    return ProjectionExecutionResult(
        source_revision=result.source_revision,
        projection_revision=result.projection_revision,
        projected=result.projected,
        audit=_audit(result.audit),
        issues=tuple(_issue(issue) for issue in result.issues),
        summary=tuple(_summary(item) for item in result.summary),
    )


def _optional_audit(record) -> ProjectionAuditRecord | None:
    return _audit(record) if record is not None else None


def _audit(record) -> ProjectionAuditRecord:
    return ProjectionAuditRecord(
        actor=record.actor,
        occurred_at=record.occurred_at_utc,
    )


def _issue(issue) -> ProjectionIssue:
    return ProjectionIssue(
        code=issue.code,
        message=issue.message,
        level=issue.level,
        path=issue.path,
    )


def _summary(item) -> ProjectionSummaryItem:
    return ProjectionSummaryItem(label=item.label, value=item.value)
