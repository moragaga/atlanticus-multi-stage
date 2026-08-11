from __future__ import annotations

from flask import Flask

from atlanticus.web.assets import AssetLayer
from atlanticus.web.health import HealthRegistry
from atlanticus.web.index import IndexContribution
from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry


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


def _register_services(services: ServiceRegistry) -> None:
    services.add('reference.application_name', 'Atlanticus Web')
    services.add(
        'reference.message',
        'Flask, Dash Pages and web modules were composed successfully.',
    )


def _register_health_checks(health: HealthRegistry, _services: ServiceRegistry) -> None:
    health.add('reference', lambda: True)


def _register_middlewares(server: Flask, _services: ServiceRegistry) -> None:
    @server.after_request
    def add_reference_header(response):
        response.headers['X-Atlanticus-Reference'] = '1'
        return response


def _register_routes(server: Flask, services: ServiceRegistry) -> None:
    @server.get('/api/reference')
    def reference_status() -> tuple[dict[str, str], int]:
        return {
            'status': 'ok',
            'message': services.require('reference.message', str),
        }, 200
