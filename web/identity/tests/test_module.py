from pathlib import Path

import pytest
from flask import Flask, Request

from atlanticus.web.identity.access import (
    ACCESS_RUNTIME_SERVICE_KEY,
    AccessDecision,
    AccessResolver,
    AccessRuntime,
    AccessStatus,
)
from atlanticus.web.identity.errors import (
    IdentityAuthenticationError,
    IdentityConfigurationError,
    IdentityProviderUnavailableError,
)
from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.identity.module import create_identity_module
from atlanticus.web.identity.provider import IdentityProvider
from atlanticus.web.services import ServiceRegistry


class CountingProvider(IdentityProvider):
    def __init__(self, *, mode: str = 'ok', production_ready: bool = True) -> None:
        self.calls = 0
        self.mode = mode
        self._production_ready = production_ready

    @property
    def key(self) -> str:
        return 'test'

    @property
    def production_ready(self) -> bool:
        return self._production_ready

    def validate_configuration(self) -> None:
        return None

    def resolve(self, request: Request) -> AuthenticatedIdentity:
        del request
        self.calls += 1
        if self.mode == 'invalid':
            raise IdentityAuthenticationError('Invalid identity')
        if self.mode == 'unavailable':
            raise IdentityProviderUnavailableError('Provider unavailable')
        return AuthenticatedIdentity(provider_key='test', issuer='test', subject_id='subject')


class CountingResolver(AccessResolver):
    def __init__(self, *, disabled: bool = False) -> None:
        self.calls = 0
        self.disabled = disabled

    def resolve(self, identity: AuthenticatedIdentity) -> AccessDecision:
        del identity
        self.calls += 1
        if self.disabled:
            return AccessDecision(status=AccessStatus.USER_DISABLED, user_id='user-1')
        return AccessDecision(status=AccessStatus.READY, user_id=f'user-{self.calls}')


def _build_server(
    monkeypatch,
    tmp_path: Path,
    provider: IdentityProvider,
    resolver: AccessResolver,
) -> tuple[Flask, ServiceRegistry]:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('ATLANTICUS_ENVIRONMENT', 'local')
    monkeypatch.setenv('ATLANTICUS_IDENTITY_PROVIDER', provider.key)
    module = create_identity_module(provider, access_resolver=resolver)
    services = ServiceRegistry()
    assert module.register_services is not None
    module.register_services(services)
    services.freeze()
    server = Flask(__name__)
    assert module.register_middlewares is not None
    module.register_middlewares(server, services)
    assert module.register_routes is not None
    module.register_routes(server, services)

    @server.get('/')
    def home():
        return 'home'

    @server.get('/api/snapshot')
    def snapshot():
        current = services.require(ACCESS_RUNTIME_SERVICE_KEY, AccessRuntime).current()
        return {
            'load_id': current.load_id,
            'status': current.status.value,
            'user_id': current.user_id,
        }

    @server.post('/_dash-update-component')
    def callback():
        return {'ok': True}

    return server, services


def test_page_load_resolves_once_callbacks_reuse_and_reload_refreshes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    provider = CountingProvider()
    resolver = CountingResolver()
    server, _ = _build_server(monkeypatch, tmp_path, provider, resolver)
    client = server.test_client()

    first = client.get('/', headers={'Accept': 'text/html'})
    first_snapshot = client.get('/api/snapshot').get_json()
    callback = client.post('/_dash-update-component')
    second_snapshot = client.get('/api/snapshot').get_json()
    reload_response = client.get('/', headers={'Accept': 'text/html'})
    reloaded_snapshot = client.get('/api/snapshot').get_json()

    assert first.status_code == 200
    assert callback.status_code == 200
    assert reload_response.status_code == 200
    assert provider.calls == 2
    assert resolver.calls == 2
    assert first_snapshot == second_snapshot
    assert first_snapshot['load_id'] != reloaded_snapshot['load_id']
    assert first_snapshot['user_id'] == 'user-1'
    assert reloaded_snapshot['user_id'] == 'user-2'


def test_invalid_identity_redirects_to_neutral_page_without_second_resolution(
    monkeypatch,
    tmp_path: Path,
) -> None:
    provider = CountingProvider(mode='invalid')
    server, _ = _build_server(monkeypatch, tmp_path, provider, CountingResolver())

    response = server.test_client().get('/', headers={'Accept': 'text/html'}, follow_redirects=True)

    assert response.status_code == 401
    assert 'Credenciales no válidas' in response.get_data(as_text=True)
    assert provider.calls == 1


def test_disabled_user_redirects_to_neutral_page(monkeypatch, tmp_path: Path) -> None:
    provider = CountingProvider()
    resolver = CountingResolver(disabled=True)
    server, _ = _build_server(monkeypatch, tmp_path, provider, resolver)

    response = server.test_client().get('/', headers={'Accept': 'text/html'}, follow_redirects=True)

    assert response.status_code == 403
    assert 'Usuario deshabilitado' in response.get_data(as_text=True)
    assert provider.calls == 1
    assert resolver.calls == 1


def test_provider_unavailable_is_not_reported_as_invalid_credentials(
    monkeypatch,
    tmp_path: Path,
) -> None:
    provider = CountingProvider(mode='unavailable')
    server, _ = _build_server(monkeypatch, tmp_path, provider, CountingResolver())

    response = server.test_client().get('/', headers={'Accept': 'text/html'}, follow_redirects=True)

    assert response.status_code == 503
    assert 'Servicio no disponible' in response.get_data(as_text=True)
    assert 'Credenciales no válidas' not in response.get_data(as_text=True)


def test_local_session_secret_is_persisted_for_multiple_workers(
    monkeypatch,
    tmp_path: Path,
) -> None:
    provider = CountingProvider()
    resolver = CountingResolver()
    first, _ = _build_server(monkeypatch, tmp_path, provider, resolver)
    first_secret = first.secret_key
    second, _ = _build_server(monkeypatch, tmp_path, CountingProvider(), CountingResolver())

    assert first_secret
    assert second.secret_key == first_secret
    assert (tmp_path / '.runtime' / 'identity' / 'session.key').is_file()


def test_production_accepts_any_production_ready_provider(monkeypatch) -> None:
    monkeypatch.setenv('ATLANTICUS_ENVIRONMENT', 'production')
    monkeypatch.setenv('ATLANTICUS_IDENTITY_PROVIDER', 'test')
    module = create_identity_module(CountingProvider(production_ready=True))
    services = ServiceRegistry()

    assert module.register_services is not None
    module.register_services(services)


def test_production_rejects_local_only_provider(monkeypatch) -> None:
    monkeypatch.setenv('ATLANTICUS_ENVIRONMENT', 'production')
    monkeypatch.setenv('ATLANTICUS_IDENTITY_PROVIDER', 'test')
    module = create_identity_module(CountingProvider(production_ready=False))
    services = ServiceRegistry()

    assert module.register_services is not None
    with pytest.raises(IdentityConfigurationError, match='not allowed in production'):
        module.register_services(services)


def test_production_requires_flask_secret_key(monkeypatch) -> None:
    monkeypatch.setenv('ATLANTICUS_ENVIRONMENT', 'production')
    monkeypatch.setenv('ATLANTICUS_IDENTITY_PROVIDER', 'test')
    module = create_identity_module(CountingProvider(production_ready=True))
    services = ServiceRegistry()
    assert module.register_services is not None
    module.register_services(services)
    services.freeze()
    server = Flask(__name__)

    assert module.register_middlewares is not None
    with pytest.raises(IdentityConfigurationError, match='SECRET_KEY'):
        module.register_middlewares(server, services)
