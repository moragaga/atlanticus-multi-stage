from __future__ import annotations

from flask import Flask

from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule
from atlanticus.web.navigation import resolve_navigation_from_services
from atlanticus.web.services import ServiceRegistry


def create_reference_module() -> WebModule:
    return WebModule(
        name='reference',
        page_packages=('ada_ui_reference.pages',),
        asset_layers=(
            AssetLayer(
                name='ada_ui_reference',
                load_order=900,
                package='ada_ui_reference',
            ),
        ),
        register_routes=_register_routes,
    )


def _register_routes(server: Flask, services: ServiceRegistry) -> None:
    @server.get('/api/navigation')
    def navigation_status() -> tuple[dict[str, object], int]:
        menu = resolve_navigation_from_services(services)
        return {
            'user': {
                'display_name': menu.user.display_name,
                'profile_key': menu.user.profile_key,
                'profile_label': menu.user.profile_label,
                'profile_color': menu.user.profile_color,
                'avatar_text': menu.user.avatar_text,
            },
            'links': [link.key for link in menu.links],
            'groups': [
                {'key': group.key, 'links': [link.key for link in group.links]}
                for group in menu.groups
            ],
        }, 200
