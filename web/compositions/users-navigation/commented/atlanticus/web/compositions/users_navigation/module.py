# Espejo pedagógico: esta composición registra el provider que conecta Identity/Users con Navigation.
from __future__ import annotations

from atlanticus.web.compositions.users_navigation.adapter import principal_from_effective_user
from atlanticus.web.identity.access import ACCESS_RUNTIME_SERVICE_KEY, AccessRuntime
from atlanticus.web.modules import WebModule
from atlanticus.web.navigation import (
    NAVIGATION_PRINCIPAL_PROVIDER_SERVICE_KEY,
    NavigationPrincipalProvider,
)
from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.runtime import USERS_RUNTIME_SERVICE_KEY, UsersRuntime


def create_users_navigation_module() -> WebModule:
    def register_services(services: ServiceRegistry) -> None:
        services.add(
            NAVIGATION_PRINCIPAL_PROVIDER_SERVICE_KEY,
            NavigationPrincipalProvider(
                lambda: principal_from_effective_user(
                    services.require(USERS_RUNTIME_SERVICE_KEY, UsersRuntime).current(
                        services.require(ACCESS_RUNTIME_SERVICE_KEY, AccessRuntime).current()
                    )
                )
            ),
        )

    return WebModule(
        name='users-navigation',
        register_services=register_services,
    )
