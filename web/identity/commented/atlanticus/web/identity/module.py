# El middleware refresca solo documentos HTML y excluye callbacks, APIs, assets y health.
from __future__ import annotations

from flask import Flask, redirect, request

from atlanticus.web.environment import resolve_environment
from atlanticus.web.identity.access import (
    ACCESS_RUNTIME_SERVICE_KEY,
    AccessResolver,
    AccessRuntime,
    AccessStatus,
    AuthenticatedAccessResolver,
)
from atlanticus.web.identity.bootstrap import AccessBootstrap
from atlanticus.web.identity.configuration import resolve_identity_provider_key
from atlanticus.web.identity.errors import (
    IdentityConfigurationError,
    IdentityProviderUnavailableError,
)
from atlanticus.web.identity.pages import (
    identity_unavailable_response,
    invalid_identity_response,
    user_disabled_response,
)
from atlanticus.web.identity.provider import IdentityProvider
from atlanticus.web.identity.session import configure_identity_session
from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry

ACCESS_BOOTSTRAP_SERVICE_KEY = 'atlanticus.web.identity.bootstrap'
_ACCESS_PREFIX = '/_atlanticus/access'
_INVALID_PATH = f'{_ACCESS_PREFIX}/invalid-identity'
_DISABLED_PATH = f'{_ACCESS_PREFIX}/user-disabled'
_UNAVAILABLE_PATH = f'{_ACCESS_PREFIX}/unavailable'


def create_identity_module(
    provider: IdentityProvider,
    *,
    access_resolver: AccessResolver | None = None,
) -> WebModule:
    resolver = access_resolver or AuthenticatedAccessResolver()

    def register_services(services: ServiceRegistry) -> None:
        selected_provider = resolve_identity_provider_key()
        if selected_provider != provider.key:
            raise IdentityConfigurationError(
                f'Configured identity provider {selected_provider!r} does not match '
                f'composed provider {provider.key!r}'
            )
        if resolve_environment().is_production and not provider.production_ready:
            raise IdentityConfigurationError(
                f'Identity provider {provider.key!r} is not allowed in production'
            )
        provider.validate_configuration()
        runtime = AccessRuntime()
        services.add(ACCESS_RUNTIME_SERVICE_KEY, runtime)
        services.add(
            ACCESS_BOOTSTRAP_SERVICE_KEY,
            AccessBootstrap(provider=provider, resolver=resolver, runtime=runtime),
        )

    def register_middlewares(server: Flask, services: ServiceRegistry) -> None:
        configure_identity_session(server)
        provider.configure(server)
        bootstrap = services.require(ACCESS_BOOTSTRAP_SERVICE_KEY, AccessBootstrap)

        @server.before_request
        def bootstrap_page_access():
            if not _is_page_document_request():
                return None
            try:
                snapshot = bootstrap.refresh(request)
            except IdentityProviderUnavailableError:
                return redirect(_UNAVAILABLE_PATH)
            if snapshot.status is AccessStatus.INVALID_IDENTITY:
                return redirect(_INVALID_PATH)
            if snapshot.status is AccessStatus.USER_DISABLED:
                return redirect(_DISABLED_PATH)
            return None

    def register_routes(server: Flask, _services: ServiceRegistry) -> None:
        server.add_url_rule(
            _INVALID_PATH,
            'atlanticus_identity_invalid',
            invalid_identity_response,
            methods=['GET'],
        )
        server.add_url_rule(
            _DISABLED_PATH,
            'atlanticus_identity_disabled',
            user_disabled_response,
            methods=['GET'],
        )
        server.add_url_rule(
            _UNAVAILABLE_PATH,
            'atlanticus_identity_unavailable',
            identity_unavailable_response,
            methods=['GET'],
        )

    return WebModule(
        name='identity',
        register_services=register_services,
        register_middlewares=register_middlewares,
        register_routes=register_routes,
    )


def _is_page_document_request() -> bool:
    if request.method != 'GET':
        return False
    path = request.path
    excluded_prefixes = (
        _ACCESS_PREFIX,
        '/_dash',
        '/assets/',
        '/health/',
        '/api/',
    )
    if path.startswith(excluded_prefixes):
        return False
    best = request.accept_mimetypes.best_match(['text/html', 'application/json'])
    return best == 'text/html'
