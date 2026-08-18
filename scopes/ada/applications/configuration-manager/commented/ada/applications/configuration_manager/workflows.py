# Espejo pedagógico: conserva la misma lógica del archivo productivo.
# Los comentarios documentan la responsabilidad sin cambiar el comportamiento.
# Adapta Tools al ciclo genérico Draft, Source y Projection del Manager.
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


class ToolManagerWorkflowAdapter:
    def __init__(self, services: ToolConfigurationServices) -> None:
        self._services = services
        self._workflow = services.projection_workflow
        self._administration = services.administration

    def get_status(self) -> ProjectionStatus:
        status = self._workflow.get_status()
        return ProjectionStatus(
            source_revision=status.source_revision,
            source_audit=(
                _audit(status.source_audit)
                if status.source_audit is not None
                else None
            ),
            active_revision=status.active_revision,
            active_source_revision=status.active_source_revision,
            projection_audit=(
                _audit(status.projection_audit)
                if status.projection_audit is not None
                else None
            ),
        )

    def validate_draft(self, payload: dict[str, object]) -> DraftValidationResult:
        catalog = ToolConfigurationCatalog.from_document(payload)
        result = self._administration.validate_catalog(catalog)
        return DraftValidationResult(
            draft_revision=result.draft_revision,
            valid=result.valid,
            audit=_audit(result.audit),
            issues=tuple(_issue(issue) for issue in result.issues),
            summary=tuple(_summary(item) for item in result.summary),
        )

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
        return SourcePublicationResult(
            source_revision=result.source_revision,
            published=result.published,
            audit=_audit(result.audit),
            summary=tuple(_summary(item) for item in result.summary),
        )

    def project(self, expected_source_revision: str) -> ProjectionExecutionResult:
        result = self._workflow.project(expected_source_revision)
        return ProjectionExecutionResult(
            source_revision=result.source_revision,
            projection_revision=result.projection_revision,
            projected=result.projected,
            audit=_audit(result.audit),
            issues=tuple(_issue(issue) for issue in result.issues),
            summary=tuple(_summary(item) for item in result.summary),
        )

    def load_revision(self, revision: str) -> dict[str, object]:
        return self._administration.load_revision_catalog(revision).to_document()

    def list_history(self, *, limit: int = 20) -> tuple[RevisionHistoryEntry, ...]:
        status = self._workflow.get_status()
        result = []
        for bundle in self._administration.list_history(limit=limit):
            result.append(
                RevisionHistoryEntry(
                    revision=bundle.revision,
                    saved_by=bundle.saved_by,
                    saved_at=bundle.saved_at_utc,
                    active=bundle.revision == status.active_source_revision,
                    current=bundle.revision == status.source_revision,
                )
            )
        return tuple(result)


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
