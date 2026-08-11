# Registra el menú ya resuelto como servicio de la aplicación web.
from __future__ import annotations

from atlanticus.web.modules import WebModule
from atlanticus.web.navigation.models import NavigationMenu
from atlanticus.web.services import ServiceRegistry

NAVIGATION_SERVICE_KEY = 'atlanticus.web.navigation.menu'


def create_navigation_module(menu: NavigationMenu) -> WebModule:
    def register_services(services: ServiceRegistry) -> None:
        services.add(NAVIGATION_SERVICE_KEY, menu)

    return WebModule(
        name='navigation',
        register_services=register_services,
    )
