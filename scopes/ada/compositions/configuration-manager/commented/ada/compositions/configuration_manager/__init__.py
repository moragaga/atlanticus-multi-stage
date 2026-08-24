# Espejo comentado: misma lógica productiva con notas pedagógicas en español.
from ada.compositions.configuration_manager.backends import (
    ConfigurationBackendSelection,
    ConfigurationHistoryBackend,
    ConfigurationProjectionBackend,
    create_configuration_manager_dependencies,
    create_configuration_runtime_projection,
    open_configuration_manager_sharepoint_infrastructure,
    resolve_configuration_backend_selection,
)
from ada.compositions.configuration_manager.composition import (
    NAVIGATION_WORKFLOW_SERVICE,
    TOOLS_WORKFLOW_SERVICE,
    USERS_WORKFLOW_SERVICE,
    build_configuration_manager_surface,
)
from ada.compositions.configuration_manager.dependencies import (
    ConfigurationManagerDependencies,
)
from ada.compositions.configuration_manager.principal import (
    EffectiveUserManagerPrincipalProvider,
    create_manager_principal_binding_module,
    manager_principal_from_effective_user,
)
from ada.compositions.configuration_manager.workflows import (
    NavigationManagerWorkflowAdapter,
    ToolManagerWorkflowAdapter,
    UsersManagerWorkflowAdapter,
)

__all__ = [
    'ConfigurationBackendSelection',
    'ConfigurationHistoryBackend',
    'ConfigurationProjectionBackend',
    'EffectiveUserManagerPrincipalProvider',
    'create_configuration_manager_dependencies',
    'create_configuration_runtime_projection',
    'open_configuration_manager_sharepoint_infrastructure',
    'create_manager_principal_binding_module',
    'manager_principal_from_effective_user',
    'resolve_configuration_backend_selection',
    'ConfigurationManagerDependencies',
    'NAVIGATION_WORKFLOW_SERVICE',
    'NavigationManagerWorkflowAdapter',
    'TOOLS_WORKFLOW_SERVICE',
    'ToolManagerWorkflowAdapter',
    'USERS_WORKFLOW_SERVICE',
    'UsersManagerWorkflowAdapter',
    'build_configuration_manager_surface',
]
