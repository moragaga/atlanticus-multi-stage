# Espejo pedagógico del módulo productivo.
# Los comentarios explican responsabilidades sin alterar estructura ni comportamiento.
from __future__ import annotations

from flask import Flask

from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule
from atlanticus.web.navigation import resolve_navigation_from_services
from atlanticus.web.services import ServiceRegistry


# Encapsula la operación create reference module para mantener esta responsabilidad aislada.
def create_reference_module() -> WebModule:
    return WebModule(
        name='reference',
        page_packages=('ada.applications.reference.pages',),
        asset_layers=(
            AssetLayer(
                name='ada_ui_reference',
                load_order=900,
                package='ada.applications.reference',
            ),
        ),
        register_routes=_register_routes,
    )


# Encapsula la operación register routes para mantener esta responsabilidad aislada.
def _register_routes(server: Flask, services: ServiceRegistry) -> None:
    @server.get('/api/navigation')
    def navigation_status() -> tuple[dict[str, object], int]:
        menu = resolve_navigation_from_services(services)
        return {
            'user': {
                'display_name': menu.user.display_name,
                'profile_key': menu.user.profile_key,
                'profile_label': menu.user.profile_label,
                'profile_background_color': menu.user.profile_background_color,
                'profile_text_color': menu.user.profile_text_color,
                'avatar_background_color': menu.user.avatar_background_color,
                'avatar_text_color': menu.user.avatar_text_color,
                'avatar_text': menu.user.avatar_text,
            },
            'links': [link.key for link in menu.links],
            'groups': [
                {'key': group.key, 'links': [link.key for link in group.links]}
                for group in menu.groups
            ],
        }, 200
