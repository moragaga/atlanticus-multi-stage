from atlanticus.web.manager.authorization import ManagerAuthorizationPolicy
from atlanticus.web.manager.errors import ManagerAuthorizationError, ManagerProjectionError
from atlanticus.web.manager.models import ManagerModule, ManagerPrincipal
from atlanticus.web.manager.projection import (
    ConfigurationLifecycleWorkflow,
    DraftValidationResult,
    ProjectionExecutionResult,
    ProjectionStatus,
    RevisionHistoryEntry,
    RevisionHistoryWorkflow,
    SourcePublicationResult,
)
from atlanticus.web.manager.registry import ManagerModuleRegistry
from atlanticus.web.services import ServiceRegistry


class ManagerProjectionCoordinator:
    def __init__(
        self,
        *,
        registry: ManagerModuleRegistry,
        services: ServiceRegistry,
        authorization: ManagerAuthorizationPolicy,
    ) -> None:
        self._registry = registry
        self._services = services
        self._authorization = authorization

    def get_status(self, module_key: str, principal: ManagerPrincipal) -> ProjectionStatus:
        module, workflow = self._resolve(module_key)
        if not self._authorization.can_view(principal, module):
            raise ManagerAuthorizationError('Manager module access is denied')
        return workflow.get_status()

    def validate_draft(
        self,
        module_key: str,
        principal: ManagerPrincipal,
        payload: dict[str, object],
    ) -> DraftValidationResult:
        module, workflow = self._resolve(module_key)
        if not self._authorization.can_validate(principal, module):
            raise ManagerAuthorizationError('Manager validation access is denied')
        return workflow.validate_draft(payload)

    def publish_draft(
        self,
        module_key: str,
        principal: ManagerPrincipal,
        payload: dict[str, object],
        expected_source_revision: str | None,
    ) -> SourcePublicationResult:
        module, workflow = self._resolve(module_key)
        if not self._authorization.can_publish(principal, module):
            raise ManagerAuthorizationError('Manager source publication access is denied')
        return workflow.publish_draft(payload, expected_source_revision)

    def project(
        self,
        module_key: str,
        principal: ManagerPrincipal,
        expected_source_revision: str,
    ) -> ProjectionExecutionResult:
        module, workflow = self._resolve(module_key)
        if not self._authorization.can_project(principal, module):
            raise ManagerAuthorizationError('Manager projection access is denied')
        revision = expected_source_revision.strip()
        if not revision:
            raise ManagerProjectionError('Expected source revision must not be empty')
        return workflow.project(revision)

    def can_load_history(self, module_key: str, principal: ManagerPrincipal) -> bool:
        module, workflow = self._resolve(module_key)
        return isinstance(workflow, RevisionHistoryWorkflow) and self._authorization.can_view(
            principal, module
        )

    def load_history_revision(
        self,
        module_key: str,
        principal: ManagerPrincipal,
        revision: str,
    ) -> dict[str, object]:
        module, workflow = self._resolve(module_key)
        if not isinstance(workflow, RevisionHistoryWorkflow):
            raise ManagerProjectionError('Manager workflow does not support history loading')
        if not self._authorization.can_view(principal, module):
            raise ManagerAuthorizationError('Manager module access is denied')
        normalized = revision.strip()
        if not normalized:
            raise ManagerProjectionError('History revision must not be empty')
        return workflow.load_revision(normalized)

    def list_history(
        self,
        module_key: str,
        principal: ManagerPrincipal,
        *,
        limit: int = 20,
    ) -> tuple[RevisionHistoryEntry, ...]:
        module, workflow = self._resolve(module_key)
        if not self._authorization.can_view(principal, module):
            raise ManagerAuthorizationError('Manager module access is denied')
        if not isinstance(workflow, RevisionHistoryWorkflow):
            return ()
        return workflow.list_history(limit=limit)

    def _resolve(self, module_key: str) -> tuple[ManagerModule, ConfigurationLifecycleWorkflow]:
        module = self._registry.require(module_key)
        workflow = self._services.require(module.workflow_service)
        if not isinstance(workflow, ConfigurationLifecycleWorkflow):
            raise ManagerProjectionError('Manager lifecycle workflow has an invalid contract')
        return module, workflow
