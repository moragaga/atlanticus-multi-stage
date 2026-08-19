from __future__ import annotations

from ada.compositions.web_application import create_ada_application_modules
from ada.compositions.web_bootstrap.models import (
    AdaConfigurationBackends,
    AdaCosmosBindings,
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
from atlanticus.web.identity.provider import IdentityProvider
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
    CosmosProfileCatalog,
    CosmosUsersGatewayAdapter,
    CosmosUsersProjectionRepository,
    UsersCosmosProfileCache,
    UsersCosmosSource,
)
from atlanticus.web.users.runtime import UsersRuntime


def create_ada_web_bootstrap(
    *,
    metadata: ApplicationMetadata,
    identity_provider: IdentityProvider,
    infrastructure: WebRuntimeInfrastructure,
    bindings: AdaCosmosBindings,
    users_runtime: UsersRuntime | None = None,
) -> AdaWebBootstrap:
    if not isinstance(metadata, ApplicationMetadata):
        raise TypeError('metadata must be ApplicationMetadata')
    if not isinstance(identity_provider, IdentityProvider):
        raise TypeError('identity_provider must be IdentityProvider')
    if not isinstance(infrastructure, WebRuntimeInfrastructure):
        raise TypeError('infrastructure must be WebRuntimeInfrastructure')
    if not isinstance(bindings, AdaCosmosBindings):
        raise TypeError('bindings must be AdaCosmosBindings')
    if users_runtime is not None and not isinstance(users_runtime, UsersRuntime):
        raise TypeError('users_runtime must be UsersRuntime or None')

    runtime = users_runtime or UsersRuntime()
    users_client = infrastructure.cosmos(bindings.users)
    activity_client = infrastructure.cosmos(bindings.activity)
    navigation_client = infrastructure.cosmos(bindings.navigation)

    users_gateway = CosmosUsersGatewayAdapter(client=users_client)
    profile_cache = UsersCosmosProfileCache(users_gateway)
    profiles = CosmosProfileCatalog(profile_cache)
    users_source = UsersCosmosSource(gateway=users_gateway, profiles=profile_cache)
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
    activity_repository = CosmosUserActivityRepository(
        client=activity_client,
        patch_operation_factory=CosmosPatchOperation,
    )
    modules = create_ada_application_modules(
        metadata=metadata,
        identity_provider=identity_provider,
        users_source=users_source,
        users_runtime=runtime,
        profiles=profiles,
        navigation_provider=navigation_provider,
        activity_repository=activity_repository,
    )
    return AdaWebBootstrap(
        infrastructure=infrastructure,
        bindings=bindings,
        modules=modules,
        users_runtime=runtime,
        users_source=users_source,
        profiles=profiles,
        navigation_provider=navigation_provider,
        activity_repository=activity_repository,
    )


def create_ada_configuration_backends(
    *,
    infrastructure: WebRuntimeInfrastructure,
    bindings: AdaCosmosBindings,
) -> AdaConfigurationBackends:
    if not isinstance(infrastructure, WebRuntimeInfrastructure):
        raise TypeError('infrastructure must be WebRuntimeInfrastructure')
    if not isinstance(bindings, AdaCosmosBindings):
        raise TypeError('bindings must be AdaCosmosBindings')

    users_client = infrastructure.cosmos(bindings.users)
    navigation_client = infrastructure.cosmos(bindings.navigation)
    tools_client = infrastructure.cosmos(bindings.tools)
    gateway = infrastructure.sharepoint()
    paths = infrastructure.sharepoint_paths
    return AdaConfigurationBackends(
        users_source=SharePointUsersConfigurationStore(
            gateway=gateway,
            settings=SharePointUsersConfigurationSettings(
                relative_path=paths.users_relative_path,
            ),
        ),
        users_projection=CosmosUsersProjectionRepository(client=users_client),
        users_discovered=CosmosDiscoveredUsersSource(client=users_client),
        navigation_source=SharePointNavigationConfigurationStore(
            gateway=gateway,
            settings=SharePointNavigationConfigurationSettings(
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
