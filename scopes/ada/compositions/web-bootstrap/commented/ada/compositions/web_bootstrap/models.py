from __future__ import annotations

from dataclasses import dataclass

from ada.configuration.tools.adapters import (
    CosmosToolProjectionRepository,
    SharePointToolConfigurationStore,
)
from atlanticus.web.compositions.runtime_infrastructure import WebRuntimeInfrastructure
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
    CosmosProfileCatalog,
    CosmosUsersProjectionRepository,
    UsersCosmosSource,
)
from atlanticus.web.users.runtime import UsersRuntime


class AdaWebBootstrapError(RuntimeError):
    # Error de composición/bootstrap ADA, separado de los errores de cada capability.
    pass


@dataclass(frozen=True, slots=True)
class AdaCosmosBindings:
    # Cada campo identifica una conexión lógica resuelta por la solución, no por Atlanticus.
    users: str
    activity: str
    navigation: str
    tools: str

    def __post_init__(self) -> None:
        # Los nombres son arbitrarios, pero deben ser textos utilizables como claves del registry.
        for field_name in ('users', 'activity', 'navigation', 'tools'):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise TypeError(f'{field_name} Cosmos connection must be non-empty text')
            object.__setattr__(self, field_name, value.strip())


@dataclass(frozen=True, slots=True)
class AdaConfigurationBackends:
    # Backends de administración/sincronización: SharePoint es fuente y Cosmos proyección.
    users_source: SharePointUsersConfigurationStore
    users_projection: CosmosUsersProjectionRepository
    users_discovered: CosmosDiscoveredUsersSource
    navigation_source: SharePointNavigationConfigurationStore
    navigation_projection: CosmosNavigationProjectionRepository
    tools_source: SharePointToolConfigurationStore
    tools_projection: CosmosToolProjectionRepository


@dataclass(frozen=True, slots=True)
class AdaWebBootstrap:
    # Dependencias efectivas del runtime operativo; SharePoint no forma parte de este contrato.
    infrastructure: WebRuntimeInfrastructure
    bindings: AdaCosmosBindings
    modules: tuple[WebModule, ...]
    users_runtime: UsersRuntime
    users_source: UsersCosmosSource
    profiles: CosmosProfileCatalog
    navigation_provider: NavigationDefinitionProvider
    activity_repository: UserActivityRepository
