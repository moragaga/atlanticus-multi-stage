from __future__ import annotations

# Espejo comentado: misma lógica productiva con notas pedagógicas en español.

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from ada.compositions.configuration_manager.dependencies import ConfigurationManagerDependencies
from ada.compositions.web_bootstrap import (
    AdaConfigurationFilenames,
    AdaCosmosBindings,
    AdaRuntimeProjection,
)
from ada.configuration.tools import TOOL_COSMOS_REQUIREMENTS, compose_tool_configuration_services
from ada.configuration.tools.adapters import (
    CosmosToolProjectionRepository,
    CosmosToolProjectionSettings,
    FileToolConfigurationSettings,
    FileToolConfigurationStore,
    FileToolProjectionRepository,
    FileToolProjectionSettings,
    SharePointToolConfigurationSettings,
    SharePointToolConfigurationStore,
)
from atlanticus.web.compositions.runtime_infrastructure import (
    SharePointEnvironmentDefinition,
    WebRuntimeInfrastructure,
    resolve_sharepoint_infrastructure_settings,
)
from atlanticus.web.environment import EnvironmentReader, WebEnvironment
from atlanticus.web.errors import WebConfigurationError
from atlanticus.web.manager import ManagerPrincipalProvider
from atlanticus.web.navigation.configuration import (
    NAVIGATION_COSMOS_REQUIREMENTS,
    compose_navigation_configuration_services,
    create_projected_navigation_definition_provider,
)
from atlanticus.web.navigation.configuration.adapters import (
    CosmosNavigationProjectionRepository,
    CosmosNavigationProjectionSettings,
    FileNavigationConfigurationSettings,
    FileNavigationConfigurationStore,
    FileNavigationProjectionRepository,
    FileNavigationProjectionSettings,
    SharePointNavigationConfigurationSettings,
    SharePointNavigationConfigurationStore,
)
from atlanticus.web.users.configuration import compose_users_configuration_services
from atlanticus.web.users.configuration.adapters import (
    FileUsersConfigurationSettings,
    FileUsersConfigurationStore,
    FileUsersProjectionProfileCatalog,
    FileUsersProjectionRepository,
    MemoryDiscoveredUsersSource,
    SharePointUsersConfigurationSettings,
    SharePointUsersConfigurationStore,
)
from atlanticus.web.users.cosmos import (
    CosmosDiscoveredUsersSource,
    CosmosUsersProjectionRepository,
)

_HISTORY_BACKEND_VARIABLE = 'ATLANTICUS_CONFIGURATION_HISTORY_BACKEND'
_PROJECTION_BACKEND_VARIABLE = 'ATLANTICUS_CONFIGURATION_PROJECTION_BACKEND'
_RUNTIME_PATH_VARIABLE = 'CONFIGURATION_RUNTIME_PATH'


class ConfigurationHistoryBackend(StrEnum):
    LOCAL = 'local'
    SHAREPOINT = 'sharepoint'


class ConfigurationProjectionBackend(StrEnum):
    LOCAL = 'local'
    COSMOS = 'cosmos'


@dataclass(frozen=True, slots=True)
class ConfigurationBackendSelection:
    history: ConfigurationHistoryBackend
    projection: ConfigurationProjectionBackend

    @property
    def requires_sharepoint(self) -> bool:
        return self.history is ConfigurationHistoryBackend.SHAREPOINT


def resolve_configuration_backend_selection(
    reader: EnvironmentReader,
    environment: WebEnvironment,
) -> ConfigurationBackendSelection:
    if not isinstance(reader, EnvironmentReader):
        raise TypeError('reader must be EnvironmentReader')
    if not isinstance(environment, WebEnvironment):
        raise TypeError('environment must be WebEnvironment')

    if environment.is_production:
        history = _optional_backend(
            reader,
            _HISTORY_BACKEND_VARIABLE,
            ConfigurationHistoryBackend,
            default=ConfigurationHistoryBackend.SHAREPOINT,
        )
        projection = _optional_backend(
            reader,
            _PROJECTION_BACKEND_VARIABLE,
            ConfigurationProjectionBackend,
            default=ConfigurationProjectionBackend.COSMOS,
        )
        if history is not ConfigurationHistoryBackend.SHAREPOINT:
            raise WebConfigurationError(
                'Local configuration history is only supported in local environment'
            )
        if projection is not ConfigurationProjectionBackend.COSMOS:
            raise WebConfigurationError(
                'Local configuration projection is only supported in local environment'
            )
        return ConfigurationBackendSelection(history=history, projection=projection)

    history = _optional_backend(
        reader,
        _HISTORY_BACKEND_VARIABLE,
        ConfigurationHistoryBackend,
        default=ConfigurationHistoryBackend.LOCAL,
    )
    projection = _optional_backend(
        reader,
        _PROJECTION_BACKEND_VARIABLE,
        ConfigurationProjectionBackend,
        default=ConfigurationProjectionBackend.LOCAL,
    )
    if (
        history is ConfigurationHistoryBackend.SHAREPOINT
        and projection is ConfigurationProjectionBackend.LOCAL
    ):
        raise WebConfigurationError('SharePoint configuration history requires Cosmos projection')
    return ConfigurationBackendSelection(history=history, projection=projection)


def open_configuration_manager_sharepoint_infrastructure(
    *,
    selection: ConfigurationBackendSelection,
    environment: EnvironmentReader,
    definition: SharePointEnvironmentDefinition,
) -> WebRuntimeInfrastructure | None:
    if not isinstance(selection, ConfigurationBackendSelection):
        raise TypeError('selection must be ConfigurationBackendSelection')
    if not isinstance(environment, EnvironmentReader):
        raise TypeError('environment must be EnvironmentReader')
    if not isinstance(definition, SharePointEnvironmentDefinition):
        raise TypeError('definition must be SharePointEnvironmentDefinition')
    if not selection.requires_sharepoint:
        return None

    settings = resolve_sharepoint_infrastructure_settings(environment, definition)
    infrastructure = WebRuntimeInfrastructure(
        cosmos_connections={},
        sharepoint=settings,
    )
    infrastructure.open()
    return infrastructure


# Convierte la selección local/file en readers runtime para Profiles y Navigation.
def create_configuration_runtime_projection(
    *,
    selection: ConfigurationBackendSelection,
    environment: EnvironmentReader | None = None,
    runtime_root: str | Path | None = None,
) -> AdaRuntimeProjection | None:
    if not isinstance(selection, ConfigurationBackendSelection):
        raise TypeError('selection must be ConfigurationBackendSelection')
    if selection.projection is ConfigurationProjectionBackend.COSMOS:
        return None

    root = _runtime_root(environment, runtime_root)
    users_projection = FileUsersProjectionRepository(
        FileUsersConfigurationSettings(root=root / 'projection' / 'users')
    )
    navigation_projection = FileNavigationProjectionRepository(
        FileNavigationProjectionSettings(root=root / 'projection' / 'navigation')
    )
    return AdaRuntimeProjection(
        profiles=FileUsersProjectionProfileCatalog(users_projection),
        navigation_provider=create_projected_navigation_definition_provider(
            navigation_projection
        ),
    )


# Los workflows del Manager siguen resolviendo History y Projection de forma independiente.
def create_configuration_manager_dependencies(
    *,
    selection: ConfigurationBackendSelection,
    infrastructure: WebRuntimeInfrastructure,
    bindings: AdaCosmosBindings,
    filenames: AdaConfigurationFilenames,
    principal_provider: ManagerPrincipalProvider,
    sharepoint_infrastructure: WebRuntimeInfrastructure | None = None,
    environment: EnvironmentReader | None = None,
    runtime_root: str | Path | None = None,
) -> ConfigurationManagerDependencies:
    if not isinstance(selection, ConfigurationBackendSelection):
        raise TypeError('selection must be ConfigurationBackendSelection')
    if not isinstance(infrastructure, WebRuntimeInfrastructure):
        raise TypeError('infrastructure must be WebRuntimeInfrastructure')
    if sharepoint_infrastructure is not None and not isinstance(
        sharepoint_infrastructure, WebRuntimeInfrastructure
    ):
        raise TypeError('sharepoint_infrastructure must be WebRuntimeInfrastructure or None')
    if not isinstance(bindings, AdaCosmosBindings):
        raise TypeError('bindings must be AdaCosmosBindings')
    if not isinstance(filenames, AdaConfigurationFilenames):
        raise TypeError('filenames must be AdaConfigurationFilenames')
    if not callable(principal_provider):
        raise TypeError('principal_provider must be callable')

    def actor_provider() -> str:
        return principal_provider().display_name

    if selection.history is ConfigurationHistoryBackend.SHAREPOINT:
        if sharepoint_infrastructure is None:
            raise WebConfigurationError(
                'SharePoint configuration history requires SharePoint infrastructure'
            )
        gateway = sharepoint_infrastructure.sharepoint()
        paths = sharepoint_infrastructure.sharepoint_paths
        tools_source = SharePointToolConfigurationStore(
            gateway=gateway,
            settings=SharePointToolConfigurationSettings(
                filename=filenames.tools,
                relative_path=paths.tool_relative_path,
            ),
        )
        users_source = SharePointUsersConfigurationStore(
            gateway=gateway,
            settings=SharePointUsersConfigurationSettings(
                filename=filenames.users,
                relative_path=paths.users_relative_path,
            ),
        )
        navigation_source = SharePointNavigationConfigurationStore(
            gateway=gateway,
            settings=SharePointNavigationConfigurationSettings(
                filename=filenames.navigation,
                relative_path=paths.navigation_relative_path,
            ),
        )
    else:
        root = _runtime_root(environment, runtime_root)
        tools_source = FileToolConfigurationStore(
            FileToolConfigurationSettings(
                root=root / 'source' / 'tools',
                filename=filenames.tools,
            )
        )
        users_source = FileUsersConfigurationStore(
            FileUsersConfigurationSettings(
                root=root / 'source' / 'users',
                source_filename=filenames.users,
            )
        )
        navigation_source = FileNavigationConfigurationStore(
            FileNavigationConfigurationSettings(
                root=root / 'source' / 'navigation',
                filename=filenames.navigation,
            )
        )

    if selection.projection is ConfigurationProjectionBackend.COSMOS:
        users_client = infrastructure.cosmos(bindings.users)
        navigation_client = infrastructure.cosmos(bindings.navigation)
        tools_client = infrastructure.cosmos(bindings.tools)
        tools_projection = CosmosToolProjectionRepository(
            client=tools_client,
            settings=CosmosToolProjectionSettings(
                container_name=_single_container_name(
                    TOOL_COSMOS_REQUIREMENTS,
                    capability='Tools',
                )
            ),
        )
        users_projection = CosmosUsersProjectionRepository(client=users_client)
        users_discovered = CosmosDiscoveredUsersSource(client=users_client)
        navigation_projection = CosmosNavigationProjectionRepository(
            client=navigation_client,
            settings=CosmosNavigationProjectionSettings(
                container_name=_single_container_name(
                    NAVIGATION_COSMOS_REQUIREMENTS,
                    capability='Navigation',
                )
            ),
        )
    else:
        root = _runtime_root(environment, runtime_root)
        tools_projection = FileToolProjectionRepository(
            FileToolProjectionSettings(root=root / 'projection' / 'tools')
        )
        users_projection = FileUsersProjectionRepository(
            FileUsersConfigurationSettings(root=root / 'projection' / 'users')
        )
        users_discovered = MemoryDiscoveredUsersSource()
        navigation_projection = FileNavigationProjectionRepository(
            FileNavigationProjectionSettings(root=root / 'projection' / 'navigation')
        )

    tools = compose_tool_configuration_services(
        source=tools_source,
        publisher=tools_source,
        projection=tools_projection,
        audit_actor_provider=actor_provider,
    )
    users = compose_users_configuration_services(
        source=users_source,
        publisher=users_source,
        projection=users_projection,
        discovered=users_discovered,
        audit_actor_provider=actor_provider,
    )
    navigation = compose_navigation_configuration_services(
        source=navigation_source,
        publisher=navigation_source,
        projection=navigation_projection,
        audit_actor_provider=actor_provider,
    )
    return ConfigurationManagerDependencies(
        tools=tools,
        users=users,
        navigation=navigation,
        principal_provider=principal_provider,
        tools_source_name=_history_label(selection.history),
        tools_projection_name=_projection_label(selection.projection),
        users_source_name=_history_label(selection.history),
        users_projection_name=_projection_label(selection.projection),
        navigation_source_name=_history_label(selection.history),
        navigation_projection_name=_projection_label(selection.projection),
    )


def _runtime_root(
    environment: EnvironmentReader | None,
    runtime_root: str | Path | None,
) -> Path:
    if runtime_root is not None:
        return Path(runtime_root).expanduser()
    reader = environment or EnvironmentReader()
    configured = reader.optional(_RUNTIME_PATH_VARIABLE)
    if configured:
        return Path(configured).expanduser()
    return Path.cwd() / '.runtime' / 'configuration'


def _optional_backend(reader, variable_name, backend_type, *, default):
    value = reader.optional(variable_name)
    if value is None or value == '':
        return default
    try:
        return backend_type(value.strip().lower())
    except ValueError as error:
        options = ' or '.join(item.value for item in backend_type)
        raise WebConfigurationError(f'Invalid {variable_name}: expected {options}') from error


def _history_label(backend: ConfigurationHistoryBackend) -> str:
    if backend is ConfigurationHistoryBackend.LOCAL:
        return 'Archivo local'
    return 'SharePoint'


def _projection_label(backend: ConfigurationProjectionBackend) -> str:
    if backend is ConfigurationProjectionBackend.LOCAL:
        return 'Archivo local'
    return 'Cosmos DB'


def _single_container_name(requirements, *, capability: str) -> str:
    if len(requirements) != 1:
        raise WebConfigurationError(
            f'{capability} configuration requires exactly one Cosmos container requirement'
        )
    return requirements[0].container_name
