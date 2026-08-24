from __future__ import annotations

from dataclasses import dataclass

from ada.configuration.tools.adapters import (
    CosmosToolProjectionRepository,
    SharePointToolConfigurationStore,
)
from atlanticus.web.compositions.runtime_infrastructure import WebRuntimeInfrastructure
from atlanticus.web.identity.provider import IdentityProvider
from atlanticus.web.modules import WebModule
from atlanticus.web.navigation.api import NavigationDefinitionProvider
from atlanticus.web.navigation.configuration.adapters import (
    CosmosNavigationProjectionRepository,
    SharePointNavigationConfigurationStore,
)
from atlanticus.web.users.activity import UserActivityRepository
from atlanticus.web.users.configuration.adapters import SharePointUsersConfigurationStore
from atlanticus.web.users.cosmos import (
    CosmosDiscoveredUsersSource,
    CosmosUsersProjectionRepository,
)
from atlanticus.web.users.profiles import ProfileCatalog
from atlanticus.web.users.runtime import UsersRuntime
from atlanticus.web.users.source import UsersSource


class AdaWebBootstrapError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AdaCosmosBindings:
    users: str
    activity: str
    navigation: str
    tools: str

    def __post_init__(self) -> None:
        for field_name in ('users', 'activity', 'navigation', 'tools'):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise TypeError(f'{field_name} Cosmos connection must be non-empty text')
            object.__setattr__(self, field_name, value.strip())


@dataclass(frozen=True, slots=True)
class AdaConfigurationFilenames:
    users: str = 'users_configuration.json.gz'
    navigation: str = 'navigation_configuration.json.gz'
    tools: str = 'tool_configuration.json.gz'

    def __post_init__(self) -> None:
        for field_name in ('users', 'navigation', 'tools'):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise TypeError(f'{field_name} configuration filename must be non-empty text')
            normalized = value.strip()
            if normalized != value:
                raise ValueError(
                    f'{field_name} configuration filename must not contain surrounding whitespace'
                )
            object.__setattr__(self, field_name, normalized)


@dataclass(frozen=True, slots=True)
class AdaConfigurationBackends:
    users_source: SharePointUsersConfigurationStore
    users_projection: CosmosUsersProjectionRepository
    users_discovered: CosmosDiscoveredUsersSource
    navigation_source: SharePointNavigationConfigurationStore
    navigation_projection: CosmosNavigationProjectionRepository
    tools_source: SharePointToolConfigurationStore
    tools_projection: CosmosToolProjectionRepository


@dataclass(frozen=True, slots=True)
class AdaRuntimeProjection:
    profiles: ProfileCatalog
    navigation_provider: NavigationDefinitionProvider

    def __post_init__(self) -> None:
        if not isinstance(self.profiles, ProfileCatalog):
            raise TypeError('profiles must be ProfileCatalog')
        if not isinstance(self.navigation_provider, NavigationDefinitionProvider):
            raise TypeError('navigation_provider must be NavigationDefinitionProvider')


@dataclass(frozen=True, slots=True)
class AdaWebBootstrap:
    infrastructure: WebRuntimeInfrastructure
    bindings: AdaCosmosBindings
    modules: tuple[WebModule, ...]
    users_runtime: UsersRuntime
    identity_provider: IdentityProvider
    users_source: UsersSource
    profiles: ProfileCatalog
    navigation_provider: NavigationDefinitionProvider
    activity_repository: UserActivityRepository
