from datetime import UTC, datetime

from atlanticus.web.manager import (
    DefaultManagerAuthorizationPolicy,
    DraftValidationResult,
    ManagerModule,
    ManagerModuleGroup,
    ManagerModuleRegistry,
    ManagerPrincipal,
    ManagerProjectionCoordinator,
    ProjectionAuditRecord,
    ProjectionExecutionResult,
    ProjectionStatus,
    RevisionHistoryEntry,
    SourcePublicationResult,
    build_draft_revision,
)
from atlanticus.web.services import ServiceRegistry


class Workflow:
    def __init__(self) -> None:
        self.audit = ProjectionAuditRecord(
            actor='Admin',
            occurred_at=datetime(2026, 8, 18, 12, 0, tzinfo=UTC),
        )

    def get_status(self) -> ProjectionStatus:
        return ProjectionStatus('source', self.audit)

    def validate_draft(self, payload: dict[str, object]) -> DraftValidationResult:
        return DraftValidationResult(build_draft_revision(payload), True, self.audit)

    def publish_draft(
        self,
        payload: dict[str, object],
        expected_source_revision: str | None,
    ) -> SourcePublicationResult:
        assert expected_source_revision == 'source'
        return SourcePublicationResult(build_draft_revision(payload), True, self.audit)

    def project(self, expected_source_revision: str) -> ProjectionExecutionResult:
        return ProjectionExecutionResult(
            source_revision=expected_source_revision,
            projection_revision='projection',
            projected=True,
            audit=self.audit,
        )

    def load_revision(self, revision: str) -> dict[str, object]:
        return {'revision': revision}

    def list_history(self, *, limit: int = 20) -> tuple[RevisionHistoryEntry, ...]:
        return (
            RevisionHistoryEntry(
                revision='source',
                saved_by='Admin',
                saved_at=self.audit.occurred_at,
            ),
        )[:limit]


def test_coordinator_orchestrates_draft_publish_projection_and_history() -> None:
    module = ManagerModule(
        key='tools',
        group_key='configuration',
        title='Herramientas',
        route='/tools',
        order=10,
        layout=lambda _services: None,
        workflow_service='tools.workflow',
    )
    registry = ManagerModuleRegistry(
        (ManagerModuleGroup('configuration', 'Configuraciones', 10),),
        (module,),
    )
    services = ServiceRegistry()
    services.add('tools.workflow', Workflow())
    principal = ManagerPrincipal('local', 'Administrador local', is_local=True)
    coordinator = ManagerProjectionCoordinator(
        registry=registry,
        services=services,
        authorization=DefaultManagerAuthorizationPolicy(),
    )
    payload = {'tools': []}

    assert coordinator.get_status('tools', principal).source_revision == 'source'
    validation = coordinator.validate_draft('tools', principal, payload)
    assert validation.valid
    publication = coordinator.publish_draft('tools', principal, payload, 'source')
    assert publication.source_revision == build_draft_revision(payload)
    assert coordinator.project('tools', principal, 'source').projection_revision == 'projection'
    assert coordinator.list_history('tools', principal)[0].revision == 'source'
    assert coordinator.load_history_revision('tools', principal, 'source') == {
        'revision': 'source'
    }
