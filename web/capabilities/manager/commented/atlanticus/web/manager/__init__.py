# Exporta los contratos públicos del Manager; ManagerSurface es la frontera reutilizable y ManagerApplicationDefinition queda para hosts standalone.
from atlanticus.web.manager.authorization import (
    DefaultManagerAuthorizationPolicy,
    ManagerAuthorizationPolicy,
)
from atlanticus.web.manager.coordinator import ManagerProjectionCoordinator
from atlanticus.web.manager.errors import (
    ManagerAuthorizationError,
    ManagerDefinitionError,
    ManagerError,
    ManagerProjectionError,
)
from atlanticus.web.manager.models import (
    ManagerApplicationDefinition,
    ManagerBrand,
    ManagerBrandMark,
    ManagerModule,
    ManagerModuleAccess,
    ManagerModuleGroup,
    ManagerPrincipal,
    ManagerPrincipalProvider,
    ManagerSurfaceDefinition,
)
from atlanticus.web.manager.projection import (
    ConfigurationLifecycleWorkflow,
    DraftValidationResult,
    ManagerDraft,
    ProjectionAuditRecord,
    ProjectionExecutionResult,
    ProjectionIssue,
    ProjectionState,
    ProjectionStatus,
    ProjectionSummaryItem,
    RevisionHistoryEntry,
    RevisionHistoryWorkflow,
    SourcePublicationResult,
    build_draft_revision,
    resolve_projection_state,
)
from atlanticus.web.manager.registry import ManagerModuleRegistry
from atlanticus.web.manager.surface import ManagerSurface

__all__ = [
    'ConfigurationLifecycleWorkflow',
    'DefaultManagerAuthorizationPolicy',
    'DraftValidationResult',
    'ManagerApplicationDefinition',
    'ManagerAuthorizationError',
    'ManagerAuthorizationPolicy',
    'ManagerBrand',
    'ManagerBrandMark',
    'ManagerDefinitionError',
    'ManagerDraft',
    'ManagerError',
    'ManagerModule',
    'ManagerModuleAccess',
    'ManagerModuleGroup',
    'ManagerModuleRegistry',
    'ManagerPrincipal',
    'ManagerPrincipalProvider',
    'ManagerSurface',
    'ManagerSurfaceDefinition',
    'ManagerProjectionCoordinator',
    'ManagerProjectionError',
    'ProjectionAuditRecord',
    'ProjectionExecutionResult',
    'ProjectionIssue',
    'ProjectionState',
    'ProjectionStatus',
    'ProjectionSummaryItem',
    'RevisionHistoryEntry',
    'RevisionHistoryWorkflow',
    'SourcePublicationResult',
    'build_draft_revision',
    'resolve_projection_state',
]
