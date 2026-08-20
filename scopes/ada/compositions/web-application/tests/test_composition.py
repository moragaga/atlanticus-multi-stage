import tomllib
from datetime import UTC, datetime
from pathlib import Path

from ada.compositions.web_application import create_ada_application_modules
from atlanticus.web.identity.access import ACCESS_RUNTIME_SERVICE_KEY
from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.identity.provider import IdentityProvider
from atlanticus.web.models import ApplicationMetadata
from atlanticus.web.navigation.api import (
    NAVIGATION_DEFINITION_PROVIDER_SERVICE_KEY,
    NAVIGATION_PRINCIPAL_PROVIDER_SERVICE_KEY,
    NavigationDefinition,
    NavigationDefinitionProvider,
    NavigationLinkDefinition,
)
from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.activity import (
    USER_ACTIVITY_SERVICE_KEY,
    InMemoryUserActivityRepository,
    UserActivityEvent,
    UserActivityService,
)
from atlanticus.web.users.models import EffectiveUser, ResolvedUserRecord
from atlanticus.web.users.profiles import GUEST_PROFILE_KEY, ProfileCatalog
from atlanticus.web.users.runtime import USERS_RUNTIME_SERVICE_KEY, UsersRuntime
from atlanticus.web.users.source import UsersSource


class FakeIdentityProvider(IdentityProvider):
    @property
    def key(self) -> str:
        return 'test'

    @property
    def production_ready(self) -> bool:
        return True

    def validate_configuration(self) -> None:
        return None

    def resolve(self, request) -> AuthenticatedIdentity:
        del request
        return AuthenticatedIdentity(
            provider_key='test',
            issuer='test',
            subject_id='subject-1',
        )


class FakeUsersSource(UsersSource):
    def resolve(self, identity: AuthenticatedIdentity) -> ResolvedUserRecord | None:
        return ResolvedUserRecord(
            user_id='user-1',
            subject_id=identity.subject_id,
            display_name='Test User',
            email='test@example.com',
            enabled=True,
            profile_key=GUEST_PROFILE_KEY,
        )


def test_composition_package_has_only_transversal_dependencies() -> None:
    pyproject_path = Path(__file__).parents[1] / 'pyproject.toml'
    dependencies = tomllib.loads(pyproject_path.read_text())['project']['dependencies']

    assert dependencies
    assert all(dependency.startswith('atlanticus-web') for dependency in dependencies)


def test_identity_users_only_registers_only_base_services(monkeypatch) -> None:
    modules, services = _compose_and_register(monkeypatch)

    assert tuple(module.name for module in modules) == ('users', 'identity')
    assert services.contains(USERS_RUNTIME_SERVICE_KEY)
    assert services.contains(ACCESS_RUNTIME_SERVICE_KEY)
    assert not services.contains(NAVIGATION_DEFINITION_PROVIDER_SERVICE_KEY)
    assert not services.contains(NAVIGATION_PRINCIPAL_PROVIDER_SERVICE_KEY)
    assert not services.contains(USER_ACTIVITY_SERVICE_KEY)


def test_activity_without_navigation_uses_pathname_and_application_metadata(monkeypatch) -> None:
    repository = InMemoryUserActivityRepository()
    modules, services = _compose_and_register(
        monkeypatch,
        activity_repository=repository,
    )

    assert tuple(module.name for module in modules) == ('users', 'identity', 'user-activity')
    assert not services.contains(NAVIGATION_DEFINITION_PROVIDER_SERVICE_KEY)
    assert not services.contains(NAVIGATION_PRINCIPAL_PROVIDER_SERVICE_KEY)
    service = services.require(USER_ACTIVITY_SERVICE_KEY, UserActivityService)
    service.track(
        user=_effective_user(),
        event=_event(pathname='/status/'),
        now=datetime(2026, 8, 19, 12, 0, tzinfo=UTC),
    )
    document = repository.snapshot()[0]

    assert document.application_key == 'ada-test'
    assert document.current_route_key == '/status'
    assert document.current_pathname == '/status'


def test_navigation_without_activity_registers_navigation_and_authorization(monkeypatch) -> None:
    modules, services = _compose_and_register(
        monkeypatch,
        navigation_provider=_navigation_provider(),
    )

    assert tuple(module.name for module in modules) == (
        'users',
        'identity',
        'navigation',
        'users-navigation',
        'navigation-authorization',
    )
    assert services.contains(NAVIGATION_DEFINITION_PROVIDER_SERVICE_KEY)
    assert services.contains(NAVIGATION_PRINCIPAL_PROVIDER_SERVICE_KEY)
    assert not services.contains(USER_ACTIVITY_SERVICE_KEY)


def test_full_composition_uses_navigation_route_key_for_activity(monkeypatch) -> None:
    repository = InMemoryUserActivityRepository()
    modules, services = _compose_and_register(
        monkeypatch,
        navigation_provider=_navigation_provider(),
        activity_repository=repository,
    )

    assert tuple(module.name for module in modules) == (
        'users',
        'identity',
        'navigation',
        'users-navigation',
        'navigation-authorization',
        'user-activity',
    )
    assert services.contains(NAVIGATION_DEFINITION_PROVIDER_SERVICE_KEY)
    assert services.contains(NAVIGATION_PRINCIPAL_PROVIDER_SERVICE_KEY)
    service = services.require(USER_ACTIVITY_SERVICE_KEY, UserActivityService)
    service.track(
        user=_effective_user(),
        event=_event(pathname='/status/'),
        now=datetime(2026, 8, 19, 12, 0, tzinfo=UTC),
    )
    document = repository.snapshot()[0]

    assert document.application_key == 'ada-test'
    assert document.current_route_key == 'status'
    assert document.current_pathname == '/status'


def _compose_and_register(
    monkeypatch,
    *,
    navigation_provider: NavigationDefinitionProvider | None = None,
    activity_repository: InMemoryUserActivityRepository | None = None,
):
    monkeypatch.setenv('ATLANTICUS_ENVIRONMENT', 'local')
    modules = create_ada_application_modules(
        metadata=ApplicationMetadata(
            application_id='ada-test',
            display_name='ADA Test',
            version='0.1.0',
        ),
        identity_provider=FakeIdentityProvider(),
        users_source=FakeUsersSource(),
        users_runtime=UsersRuntime(),
        profiles=ProfileCatalog(),
        navigation_provider=navigation_provider,
        activity_repository=activity_repository,
    )
    services = ServiceRegistry()
    for module in modules:
        if module.register_services is not None:
            module.register_services(services)
    return modules, services


def _navigation_provider() -> NavigationDefinitionProvider:
    return NavigationDefinitionProvider(
        lambda: NavigationDefinition(
            links=(
                NavigationLinkDefinition(
                    key='home',
                    label='Inicio',
                    href='/',
                ),
                NavigationLinkDefinition(
                    key='status',
                    label='Status',
                    href='/status',
                    allowed_profiles=(GUEST_PROFILE_KEY,),
                ),
            )
        )
    )


def _effective_user() -> EffectiveUser:
    profile = ProfileCatalog().require(GUEST_PROFILE_KEY)
    return EffectiveUser(
        user_id='user-1',
        subject_id='subject-1',
        display_name='Test User',
        email='test@example.com',
        enabled=True,
        pending=False,
        avatar_text='TU',
        profile=profile,
    )


def _event(*, pathname: str) -> UserActivityEvent:
    return UserActivityEvent.from_payload(
        {
            'event_id': 'event-1',
            'client_session_id': 'session-1',
            'sequence': 1,
            'event_type': 'register',
            'pathname': pathname,
            'visibility_state': 'visible',
            'viewport': {'width': 1200, 'height': 800},
            'screen': {'width': 1920, 'height': 1080, 'pixel_ratio': 1},
        }
    )
