from __future__ import annotations

from atlanticus.web.modules import WebModule
from atlanticus.web.navigation.models import NavigationDefinition
from atlanticus.web.navigation.principal import (
    NAVIGATION_PRINCIPAL_PROVIDER_SERVICE_KEY,
    NavigationPrincipalProvider,
)
from atlanticus.web.navigation.resolver import NAVIGATION_DEFINITION_SERVICE_KEY
from atlanticus.web.services import ServiceRegistry


def create_navigation_module(
    definition: NavigationDefinition,
    *,
    principal_provider: NavigationPrincipalProvider | None = None,
) -> WebModule:
    def register_services(services: ServiceRegistry) -> None:
        services.add(NAVIGATION_DEFINITION_SERVICE_KEY, definition)
        if principal_provider is not None:
            services.add(
                NAVIGATION_PRINCIPAL_PROVIDER_SERVICE_KEY,
                principal_provider,
            )

    return WebModule(
        name='navigation',
        register_services=register_services,
    )
