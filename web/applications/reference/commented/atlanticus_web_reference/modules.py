# Espejo pedagógico del módulo productivo.
# Los comentarios explican responsabilidades sin alterar estructura ni comportamiento.
from __future__ import annotations

from flask import Flask

from atlanticus.web.assets import AssetLayer
from atlanticus.web.health import HealthRegistry
from atlanticus.web.identity.access import ACCESS_RUNTIME_SERVICE_KEY, AccessRuntime
from atlanticus.web.index import IndexContribution
from atlanticus.web.modules import WebModule
from atlanticus.web.navigation import resolve_navigation_from_services
from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.runtime import USERS_RUNTIME_SERVICE_KEY, UsersRuntime


# Encapsula la operación create reference module para mantener esta responsabilidad aislada.
def create_reference_module() -> WebModule:
    return WebModule(
        name='reference',
        page_packages=('atlanticus_web_reference.pages',),
        asset_layers=(
            AssetLayer(
                name='reference_application',
                load_order=900,
                package='atlanticus_web_reference',
            ),
        ),
        register_services=_register_services,
        register_health_checks=_register_health_checks,
        register_middlewares=_register_middlewares,
        register_routes=_register_routes,
        index=IndexContribution(
            head_fragments=('<meta name="theme-color" content="#0D1B2A">',),
            runtime_config={
                'enabled': True,
            },
        ),
    )


# Encapsula la operación register services para mantener esta responsabilidad aislada.
def _register_services(services: ServiceRegistry) -> None:
    services.add('reference.application_name', 'Atlanticus Web')
    services.add(
        'reference.message',
        'Flask, Dash Pages and web modules were composed successfully.',
    )


# Encapsula la operación register health checks para mantener esta responsabilidad aislada.
def _register_health_checks(health: HealthRegistry, _services: ServiceRegistry) -> None:
    health.add('reference', lambda: True)


# Encapsula la operación register middlewares para mantener esta responsabilidad aislada.
def _register_middlewares(server: Flask, _services: ServiceRegistry) -> None:
    @server.after_request
    def add_reference_header(response):
        response.headers['X-Atlanticus-Reference'] = '1'
        return response


# Encapsula la operación register routes para mantener esta responsabilidad aislada.
def _register_routes(server: Flask, services: ServiceRegistry) -> None:
    @server.get('/api/access')
    def access_status() -> tuple[dict[str, str | None], int]:
        snapshot = services.require(ACCESS_RUNTIME_SERVICE_KEY, AccessRuntime).current()
        identity = snapshot.identity
        return {
            'load_id': snapshot.load_id,
            'status': snapshot.status.value,
            'provider': identity.provider_key if identity is not None else None,
            'subject_id': identity.subject_id if identity is not None else None,
            'user_id': snapshot.user_id,
        }, 200

    @server.get('/api/user')
    def effective_user() -> tuple[dict[str, object], int]:
        access = services.require(ACCESS_RUNTIME_SERVICE_KEY, AccessRuntime).current()
        user = services.require(USERS_RUNTIME_SERVICE_KEY, UsersRuntime).current(access)
        return {
            'user_id': user.user_id,
            'display_name': user.display_name,
            'email': user.email,
            'enabled': user.enabled,
            'pending': user.pending,
            'avatar_text': user.avatar_text,
            'avatar_background_color': user.avatar_background_color,
            'avatar_text_color': user.avatar_text_color,
            'profile': {
                'key': user.profile.key,
                'label': user.profile.label,
                'background_color': user.profile.background_color,
                'text_color': user.profile.text_color,
            },
            'full_access': user.has_full_access,
        }, 200

    @server.get('/api/navigation')
    def resolved_navigation() -> tuple[dict[str, object], int]:
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
                {
                    'key': group.key,
                    'links': [link.key for link in group.links],
                }
                for group in menu.groups
            ],
        }, 200

    @server.get('/api/reference')
    def reference_status() -> tuple[dict[str, str], int]:
        return {
            'status': 'ok',
            'message': services.require('reference.message', str),
        }, 200
