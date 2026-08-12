# Espejo comentado: registra configuración global y nunca datos de un usuario particular.
from __future__ import annotations

from atlanticus.web.modules import WebModule
from atlanticus.web.navigation.models import NavigationDefinition
from atlanticus.web.navigation.resolver import (
    NAVIGATION_DEFINITION_SERVICE_KEY,
    validate_navigation_definition,
)
from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.profiles import ProfileCatalog


def create_navigation_module(
    definition: NavigationDefinition,
    *,
    profiles: ProfileCatalog,
) -> WebModule:
    validate_navigation_definition(definition, profiles)

    def register_services(services: ServiceRegistry) -> None:
        services.add(NAVIGATION_DEFINITION_SERVICE_KEY, definition)

    return WebModule(
        name='navigation',
        register_services=register_services,
    )
