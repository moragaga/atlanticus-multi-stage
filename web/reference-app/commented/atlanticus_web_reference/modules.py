# Aplicación de referencia: demuestra el contrato web sin introducir lógica de negocio real.
from __future__ import annotations

from atlanticus.web import (
    AssetLayer,
    HealthRegistry,
    IndexContribution,
    ServiceRegistry,
    WebModule,
)


# El módulo concentra sus Pages, assets, servicios, health, middleware, rutas e index en una sola declaración.
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


def _register_middlewares(server: object, _services: ServiceRegistry) -> None:
    @server.after_request
    def add_reference_header(response):
        response.headers['X-Atlanticus-Reference'] = '1'
        return response


def _register_routes(server: object, services: ServiceRegistry) -> None:
    @server.get('/api/reference')
    def reference_status() -> tuple[dict[str, str], int]:
        return {
            'status': 'ok',
            'message': services.require('reference.message', str),
        }, 200
