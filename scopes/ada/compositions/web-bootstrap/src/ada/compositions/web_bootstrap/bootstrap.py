from __future__ import annotations

from ada.compositions.web_application import create_ada_application_modules
from ada.compositions.web_bootstrap.access import create_ada_access_components
from ada.compositions.web_bootstrap.models import (
    AdaConfigurationBackends,
    AdaConfigurationFilenames,
    AdaCosmosBindings,
    AdaRuntimeProjection,
    AdaWebBootstrap,
    AdaWebBootstrapError,
)
from ada.configuration.tools import TOOL_COSMOS_REQUIREMENTS
from ada.configuration.tools.adapters import (
    CosmosToolProjectionRepository,
    CosmosToolProjectionSettings,
    SharePointToolConfigurationSettings,
    SharePointToolConfigurationStore,
)
from atlanticus.connectivity.cosmos import CosmosPatchOperation
from atlanticus.web.compositions.runtime_infrastructure import WebRuntimeInfrastructure
from atlanticus.web.environment import WebEnvironment
from atlanticus.web.models import ApplicationMetadata
from atlanticus.web.navigation.configuration import (
    NAVIGATION_COSMOS_REQUIREMENTS,
    create_projected_navigation_definition_provider,
)
from atlanticus.web.navigation.configuration.adapters import (
    CosmosNavigationProjectionRepository,
    CosmosNavigationProjectionSettings,
    SharePointNavigationConfigurationSettings,
    SharePointNavigationConfigurationStore,
)
from atlanticus.web.users.activity import CosmosUserActivityRepository
from atlanticus.web.users.configuration.adapters import (
    SharePointUsersConfigurationSettings,
    SharePointUsersConfigurationStore,
)
from atlanticus.web.users.cosmos import (
    CosmosDiscoveredUsersSource,
    CosmosUsersProjectionRepository,
)
from atlanticus.web.users.runtime import UsersRuntime


def create_ada_web_bootstrap(
    *,
    metadata: ApplicationMetadata,
    environment: WebEnvironment,
    bootstrap_admin_principal: str | None = None,
    infrastructure: WebRuntimeInfrastructure,
    bindings: AdaCosmosBindings,
    users_runtime: UsersRuntime | None = None,
    runtime_projection: AdaRuntimeProjection | None = None,
) -> AdaWebBootstrap:
    if not isinstance(metadata, ApplicationMetadata):
        raise TypeError('metadata must be ApplicationMetadata')
    if not isinstance(environment, WebEnvironment):
        raise TypeError('environment must be WebEnvironment')
    if not isinstance(infrastructure, WebRuntimeInfrastructure):
        raise TypeError('infrastructure must be WebRuntimeInfrastructure')
    if not isinstance(bindings, AdaCosmosBindings):
        raise TypeError('bindings must be AdaCosmosBindings')
    if users_runtime is not None and not isinstance(users_runtime, UsersRuntime):
        raise TypeError('users_runtime must be UsersRuntime or None')
    if runtime_projection is not None and not isinstance(runtime_projection, AdaRuntimeProjection):
        raise TypeError('runtime_projection must be AdaRuntimeProjection or None')
    if runtime_projection is not None and not environment.is_local:
        raise ValueError('runtime_projection is only supported in local environment')

    runtime = users_runtime or UsersRuntime()
    users_client = infrastructure.cosmos(bindings.users)
    activity_client = infrastructure.cosmos(bindings.activity)

    access = create_ada_access_components(
        environment=environment,
        users_client=users_client,
        bootstrap_admin_principal=(
            bootstrap_admin_principal if environment.is_production else None
        ),
        local_profiles=(runtime_projection.profiles if runtime_projection is not None else None),
    )
    if runtime_projection is None:
        navigation_client = infrastructure.cosmos(bindings.navigation)
        navigation_projection = CosmosNavigationProjectionRepository(
            client=navigation_client,
            settings=CosmosNavigationProjectionSettings(
                container_name=_single_container_name(
                    NAVIGATION_COSMOS_REQUIREMENTS,
                    capability='Navigation',
                )
            ),
        )
        navigation_provider = create_projected_navigation_definition_provider(navigation_projection)
    else:
        navigation_provider = runtime_projection.navigation_provider
    activity_repository = CosmosUserActivityRepository(
        client=activity_client,
        patch_operation_factory=CosmosPatchOperation,
    )
    modules = create_ada_application_modules(
        metadata=metadata,
        identity_provider=access.identity_provider,
        users_source=access.users_source,
        users_runtime=runtime,
        profiles=access.profiles,
        navigation_provider=navigation_provider,
        activity_repository=activity_repository,
    )
    return AdaWebBootstrap(
        infrastructure=infrastructure,
        bindings=bindings,
        modules=modules,
        users_runtime=runtime,
        identity_provider=access.identity_provider,
        users_source=access.users_source,
        profiles=access.profiles,
        navigation_provider=navigation_provider,
        activity_repository=activity_repository,
    )


def create_ada_configuration_backends(
    *,
    infrastructure: WebRuntimeInfrastructure,
    bindings: AdaCosmosBindings,
    filenames: AdaConfigurationFilenames | None = None,
) -> AdaConfigurationBackends:
    if not isinstance(infrastructure, WebRuntimeInfrastructure):
        raise TypeError('infrastructure must be WebRuntimeInfrastructure')
    if not isinstance(bindings, AdaCosmosBindings):
        raise TypeError('bindings must be AdaCosmosBindings')
    if filenames is not None and not isinstance(filenames, AdaConfigurationFilenames):
        raise TypeError('filenames must be AdaConfigurationFilenames or None')
    resolved_filenames = filenames or AdaConfigurationFilenames()

    users_client = infrastructure.cosmos(bindings.users)
    navigation_client = infrastructure.cosmos(bindings.navigation)
    tools_client = infrastructure.cosmos(bindings.tools)
    gateway = infrastructure.sharepoint()
    paths = infrastructure.sharepoint_paths
    return AdaConfigurationBackends(
        users_source=SharePointUsersConfigurationStore(
            gateway=gateway,
            settings=SharePointUsersConfigurationSettings(
                filename=resolved_filenames.users,
                relative_path=paths.users_relative_path,
            ),
        ),
        users_projection=CosmosUsersProjectionRepository(client=users_client),
        users_discovered=CosmosDiscoveredUsersSource(client=users_client),
        navigation_source=SharePointNavigationConfigurationStore(
            gateway=gateway,
            settings=SharePointNavigationConfigurationSettings(
                filename=resolved_filenames.navigation,
                relative_path=paths.navigation_relative_path,
            ),
        ),
        navigation_projection=CosmosNavigationProjectionRepository(
            client=navigation_client,
            settings=CosmosNavigationProjectionSettings(
                container_name=_single_container_name(
                    NAVIGATION_COSMOS_REQUIREMENTS,
                    capability='Navigation',
                )
            ),
        ),
        tools_source=SharePointToolConfigurationStore(
            gateway=gateway,
            settings=SharePointToolConfigurationSettings(
                filename=resolved_filenames.tools,
                relative_path=paths.tool_relative_path,
            ),
        ),
        tools_projection=CosmosToolProjectionRepository(
            client=tools_client,
            settings=CosmosToolProjectionSettings(
                container_name=_single_container_name(
                    TOOL_COSMOS_REQUIREMENTS,
                    capability='Tools',
                )
            ),
        ),
    )


def _single_container_name(requirements, *, capability: str) -> str:
    if len(requirements) != 1:
        raise AdaWebBootstrapError(
            f'{capability} bootstrap requires exactly one Cosmos container requirement'
        )
    return requirements[0].container_name
