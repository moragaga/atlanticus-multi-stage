import pytest
from flask import Flask

from atlanticus.web.errors import ServiceRegistryError, WebDefinitionError
from atlanticus.web.identity.access import (
    AccessDecision,
    AccessRuntime,
    AccessSnapshot,
    AccessStatus,
)
from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.navigation import (
    NAVIGATION_DEFINITION_SERVICE_KEY,
    NavigationDefinition,
    NavigationGroupDefinition,
    NavigationLinkDefinition,
    NavigationMenu,
    create_navigation_module,
    resolve_navigation,
    resolve_navigation_from_services,
)
from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.models import EffectiveUser
from atlanticus.web.users.module import PROFILE_CATALOG_SERVICE_KEY
from atlanticus.web.users.profiles import ProfileCatalog, ProfileDefinition
from atlanticus.web.users.runtime import USERS_RUNTIME_SERVICE_KEY, UsersRuntime


def _profiles(*, administrator_background_color: str = '#673AB7') -> ProfileCatalog:
    return ProfileCatalog(
        administrator_background_color=administrator_background_color,
        custom_profiles=(
            ProfileDefinition(key='viewer', label='Visualizador', background_color='#123456'),
            ProfileDefinition(key='analyst', label='Analista', background_color='#654321'),
        )
    )


def _user(profile_key: str) -> EffectiveUser:
    profiles = _profiles()
    return EffectiveUser(
        user_id=f'user:{profile_key}',
        subject_id=f'subject:{profile_key}',
        display_name='John Doe',
        email='john@example.com',
        enabled=True,
        pending=profile_key == 'guest',
        avatar_text='JD',
        profile=profiles.require(profile_key),
    )


def _definition() -> NavigationDefinition:
    return NavigationDefinition(
        links=(
            NavigationLinkDefinition(
                key='private',
                label='Privado',
                href='/private',
            ),
            NavigationLinkDefinition(
                key='viewer-home',
                label='Viewer',
                href='/viewer',
                allowed_profiles=('viewer',),
            ),
        ),
        groups=(
            NavigationGroupDefinition(
                key='main',
                label='Main',
                allowed_profiles=('viewer',),
                links=(
                    NavigationLinkDefinition(
                        key='inherited',
                        label='Inherited',
                        href='/inherited',
                    ),
                    NavigationLinkDefinition(
                        key='override',
                        label='Override',
                        href='/override',
                        allowed_profiles=('analyst',),
                    ),
                ),
            ),
        ),
    )


def test_full_access_profiles_receive_all_navigation_without_explicit_assignment() -> None:
    profiles = _profiles()

    local = resolve_navigation(_definition(), user=_user('local'), profiles=profiles)
    administrator = resolve_navigation(
        _definition(),
        user=_user('administrator'),
        profiles=profiles,
    )

    for menu in (local, administrator):
        assert tuple(link.key for link in menu.links) == ('private', 'viewer-home')
        assert tuple(link.key for link in menu.groups[0].links) == ('inherited', 'override')


def test_custom_profile_filters_links_and_child_can_override_group_profiles() -> None:
    profiles = _profiles()

    viewer = resolve_navigation(_definition(), user=_user('viewer'), profiles=profiles)
    analyst = resolve_navigation(_definition(), user=_user('analyst'), profiles=profiles)

    assert tuple(link.key for link in viewer.links) == ('viewer-home',)
    assert tuple(link.key for link in viewer.groups[0].links) == ('inherited',)
    assert analyst.links == ()
    assert tuple(link.key for link in analyst.groups[0].links) == ('override',)


def test_guest_access_is_explicitly_configurable() -> None:
    definition = NavigationDefinition(
        links=(
            NavigationLinkDefinition(
                key='guest-home',
                label='Guest',
                href='/guest',
                allowed_profiles=('guest',),
            ),
        )
    )

    menu = resolve_navigation(definition, user=_user('guest'), profiles=_profiles())

    assert tuple(link.key for link in menu.links) == ('guest-home',)


def test_full_access_system_profiles_cannot_be_persisted_in_allowed_profiles() -> None:
    for profile_key in ('local', 'administrator'):
        with pytest.raises(WebDefinitionError, match='System profile'):
            NavigationLinkDefinition(
                key=f'link-{profile_key}',
                label='Link',
                href='/link',
                allowed_profiles=(profile_key,),
            )


def test_navigation_rejects_unknown_custom_profile_during_composition() -> None:
    definition = NavigationDefinition(
        links=(
            NavigationLinkDefinition(
                key='unknown',
                label='Unknown',
                href='/unknown',
                allowed_profiles=('not-created',),
            ),
        )
    )

    with pytest.raises(WebDefinitionError, match='not available for selection'):
        create_navigation_module(definition, profiles=_profiles())


def test_administrator_configured_color_flows_to_navigation_presentation() -> None:
    profiles = _profiles(administrator_background_color='#112233')
    user = EffectiveUser(
        user_id='administrator-1',
        subject_id='subject:administrator',
        display_name='Jane Doe',
        email='jane@example.com',
        enabled=True,
        pending=False,
        avatar_text='JD',
        profile=profiles.require('administrator'),
    )

    menu = resolve_navigation(_definition(), user=user, profiles=profiles)

    assert menu.user.profile_label == 'Administrador'
    assert menu.user.profile_background_color == '#112233'
    assert menu.user.profile_text_color == '#FFFFFF'


def test_navigation_user_is_built_from_effective_user_profile() -> None:
    menu = resolve_navigation(_definition(), user=_user('viewer'), profiles=_profiles())

    assert menu.user.display_name == 'John Doe'
    assert menu.user.profile_key == 'viewer'
    assert menu.user.profile_label == 'Visualizador'
    assert menu.user.profile_background_color == '#123456'
    assert menu.user.profile_text_color == '#FFFFFF'
    assert menu.user.avatar_background_color == '#123456'
    assert menu.user.avatar_text_color == '#FFFFFF'
    assert menu.user.avatar_text == 'JD'


def test_local_persona_visuals_do_not_replace_administrator_profile_visuals() -> None:
    profiles = _profiles(administrator_background_color='#112233')
    user = EffectiveUser(
        user_id='local-user:jane-doe',
        subject_id='local:jane-doe',
        display_name='Jane Doe',
        email='jane.doe@local.atlanticus',
        enabled=True,
        pending=False,
        avatar_text='JD',
        profile=profiles.require('administrator'),
        avatar_background_color='#C85D91',
        avatar_text_color='#FFFFFF',
        is_local=True,
    )

    menu = resolve_navigation(_definition(), user=user, profiles=profiles)

    assert menu.user.profile_background_color == '#112233'
    assert menu.user.profile_text_color == '#FFFFFF'
    assert menu.user.avatar_background_color == '#C85D91'
    assert menu.user.avatar_text_color == '#FFFFFF'


def test_navigation_module_registers_definition_not_user_menu() -> None:
    definition = _definition()
    module = create_navigation_module(definition, profiles=_profiles())
    services = ServiceRegistry()

    assert module.name == 'navigation'
    assert module.register_callbacks is None
    assert module.asset_layers == ()
    assert module.register_services is not None
    module.register_services(services)
    assert services.require(NAVIGATION_DEFINITION_SERVICE_KEY, NavigationDefinition) is definition

    with pytest.raises(ServiceRegistryError):
        services.require('atlanticus.web.navigation.menu', NavigationMenu)


def test_navigation_resolves_from_existing_access_and_users_snapshots() -> None:
    server = Flask(__name__)
    server.secret_key = 'test-only'
    profiles = _profiles()
    access_runtime = AccessRuntime()
    users_runtime = UsersRuntime()
    services = ServiceRegistry()
    definition = _definition()
    services.add('atlanticus.web.identity.access', access_runtime)
    services.add(USERS_RUNTIME_SERVICE_KEY, users_runtime)
    services.add(PROFILE_CATALOG_SERVICE_KEY, profiles)
    services.add(NAVIGATION_DEFINITION_SERVICE_KEY, definition)

    identity = AuthenticatedIdentity(
        provider_key='local',
        issuer='atlanticus-local',
        subject_id='subject:viewer',
    )
    access = AccessSnapshot.resolved(
        load_id='load-1',
        identity=identity,
        decision=AccessDecision(status=AccessStatus.READY, user_id='user:viewer'),
    )

    with server.test_request_context('/'):
        access_runtime.store(access)
        users_runtime.store(load_id='load-1', user=_user('viewer'))
        menu = resolve_navigation_from_services(services)

    assert tuple(link.key for link in menu.links) == ('viewer-home',)
    assert tuple(link.key for link in menu.groups[0].links) == ('inherited',)
