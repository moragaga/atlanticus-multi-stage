# Espejo pedagógico: esta composición registra el provider que conecta Identity/Users con Navigation.
from __future__ import annotations

from atlanticus.web.compositions.users_navigation.adapter import (
    create_users_navigation_principal_provider,
)
from atlanticus.web.identity.access import ACCESS_RUNTIME_SERVICE_KEY, AccessRuntime
from atlanticus.web.modules import WebModule
from atlanticus.web.navigation.api import NAVIGATION_PRINCIPAL_PROVIDER_SERVICE_KEY
from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.runtime import USERS_RUNTIME_SERVICE_KEY, UsersRuntime


def create_users_navigation_module() -> WebModule:
    def register_services(services: ServiceRegistry) -> None:
        services.add(
            NAVIGATION_PRINCIPAL_PROVIDER_SERVICE_KEY,
            # El provider encapsula tanto la identidad real como el fallback neutro de layout.
            create_users_navigation_principal_provider(
                access_runtime=services.require(ACCESS_RUNTIME_SERVICE_KEY, AccessRuntime),
                users_runtime=services.require(USERS_RUNTIME_SERVICE_KEY, UsersRuntime),
            ),
        )

    return WebModule(
        name='users-navigation',
        register_services=register_services,
    )
