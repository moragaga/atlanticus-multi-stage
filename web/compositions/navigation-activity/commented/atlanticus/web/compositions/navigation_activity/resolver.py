from __future__ import annotations
# Espejo pedagógico: Navigation aporta route_key estable sin convertirse en dependencia de Activity.

from atlanticus.web.navigation.authorization import (
    normalize_navigation_path,
    resolve_navigation_route,
)
from atlanticus.web.navigation.definition import (
    NAVIGATION_DEFINITION_PROVIDER_SERVICE_KEY,
    NavigationDefinitionProvider,
)
from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.activity import ActivityRouteIdentity


class NavigationActivityRouteResolver:
    def __init__(
        self,
        *,
        definition_provider: NavigationDefinitionProvider,
        home_path: str = '/',
    ) -> None:
        self._definition_provider = definition_provider
        self._home_path = normalize_navigation_path(home_path)

    def resolve(self, pathname: str) -> ActivityRouteIdentity:
        normalized = normalize_navigation_path(pathname)
        match = resolve_navigation_route(self._definition_provider.current(), normalized)
        return ActivityRouteIdentity(
            route_key=match.key if match is not None else normalized,
            pathname=normalized,
            is_application_home=normalized == self._home_path,
        )


def create_navigation_activity_route_resolver(
    services: ServiceRegistry,
) -> NavigationActivityRouteResolver:
    return NavigationActivityRouteResolver(
        definition_provider=services.require(
            NAVIGATION_DEFINITION_PROVIDER_SERVICE_KEY,
            NavigationDefinitionProvider,
        )
    )
