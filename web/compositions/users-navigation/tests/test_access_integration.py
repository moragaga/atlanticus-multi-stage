from flask import Flask, Request

from atlanticus.web.compositions.users_navigation import create_users_navigation_module
from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.identity.module import create_identity_module
from atlanticus.web.identity.provider import IdentityProvider
from atlanticus.web.navigation.api import (
    NavigationDefinition,
    NavigationLinkDefinition,
    create_navigation_authorization_module,
    create_navigation_module,
)
from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.module import create_users_module
from atlanticus.web.users.profiles import ProfileCatalog
from atlanticus.web.users.resolver import UsersAccessResolver
from atlanticus.web.users.runtime import UsersRuntime
from atlanticus.web.users.source import UsersSource


class UnknownIdentityProvider(IdentityProvider):
    @property
    def key(self) -> str:
        return 'test'

    @property
    def production_ready(self) -> bool:
        return True

    def validate_configuration(self) -> None:
        return None

    def resolve(self, request: Request) -> AuthenticatedIdentity:
        del request
        return AuthenticatedIdentity(
            provider_key='test',
            issuer='test',
            subject_id='unknown-user',
            display_name='Unknown User',
            email='unknown@example.com',
        )


class EmptyUsersSource(UsersSource):
    def resolve(self, identity: AuthenticatedIdentity):
        del identity
        return None


def test_valid_unknown_identity_becomes_guest_and_direct_url_is_authorized_by_navigation(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('ATLANTICUS_ENVIRONMENT', 'local')
    monkeypatch.setenv('ATLANTICUS_IDENTITY_PROVIDER', 'test')
    profiles = ProfileCatalog()
    users_runtime = UsersRuntime()
    modules = (
        create_users_module(users_runtime, profiles),
        create_identity_module(
            UnknownIdentityProvider(),
            access_resolver=UsersAccessResolver(
                source=EmptyUsersSource(),
                runtime=users_runtime,
                profiles=profiles,
            ),
        ),
        create_navigation_module(
            NavigationDefinition(
                links=(
                    NavigationLinkDefinition(
                        key='guest',
                        label='Guest',
                        href='/guest',
                        allowed_profiles=('guest',),
                    ),
                    NavigationLinkDefinition(
                        key='private',
                        label='Private',
                        href='/private',
                    ),
                )
            )
        ),
        create_users_navigation_module(),
        create_navigation_authorization_module(),
    )
    services = ServiceRegistry()
    for module in modules:
        if module.register_services is not None:
            module.register_services(services)
    services.freeze()
    server = Flask(__name__)
    for module in modules:
        if module.register_middlewares is not None:
            module.register_middlewares(server, services)

    @server.get('/')
    def home():
        return 'home'

    @server.get('/guest')
    def guest():
        return 'guest'

    @server.get('/private')
    def private():
        return 'private'

    client = server.test_client()

    assert client.get('/', headers={'Accept': 'text/html'}).status_code == 200
    assert client.get('/guest', headers={'Accept': 'text/html'}).status_code == 200
    denied = client.get('/private', headers={'Accept': 'text/html'})
    assert denied.status_code == 403
    assert 'Acceso denegado' in denied.get_data(as_text=True)
