import pytest

from atlanticus.web.compositions.users_navigation import (
    principal_from_effective_user,
    validate_users_navigation_profiles,
)
from atlanticus.web.errors import WebDefinitionError
from atlanticus.web.navigation import NavigationDefinition, NavigationLinkDefinition
from atlanticus.web.users.models import EffectiveUser
from atlanticus.web.users.profiles import ProfileCatalog, ProfileDefinition


def _profiles() -> ProfileCatalog:
    return ProfileCatalog(
        custom_profiles=(
            ProfileDefinition(
                key='viewer',
                label='Visualizador',
                background_color='#123456',
            ),
        )
    )


def _user(profile_key: str, *, local_visual: bool = False) -> EffectiveUser:
    profiles = _profiles()
    return EffectiveUser(
        user_id=f'user:{profile_key}',
        subject_id=f'subject:{profile_key}',
        display_name='Jane Doe',
        email='jane@example.com',
        enabled=True,
        pending=profile_key == 'guest',
        avatar_text='JD',
        profile=profiles.require(profile_key),
        avatar_background_color='#C85D91' if local_visual else None,
        avatar_text_color='#FFFFFF' if local_visual else None,
        is_local=local_visual,
    )


def test_effective_user_is_adapted_without_navigation_knowing_users() -> None:
    principal = principal_from_effective_user(_user('viewer'))

    assert principal.access_key == 'viewer'
    assert principal.unrestricted is False
    assert principal.user.profile_key == 'viewer'
    assert principal.user.profile_background_color == '#123456'
    assert principal.user.avatar_background_color == '#123456'


def test_full_access_users_become_unrestricted_navigation_principals() -> None:
    principal = principal_from_effective_user(_user('administrator', local_visual=True))

    assert principal.access_key == 'administrator'
    assert principal.unrestricted is True
    assert principal.user.profile_background_color == '#673AB7'
    assert principal.user.avatar_background_color == '#C85D91'


def test_users_catalog_validation_accepts_guest_and_custom_profiles() -> None:
    definition = NavigationDefinition(
        links=(
            NavigationLinkDefinition(
                key='guest',
                label='Guest',
                href='/guest',
                allowed_profiles=('guest',),
            ),
            NavigationLinkDefinition(
                key='viewer',
                label='Viewer',
                href='/viewer',
                allowed_profiles=('viewer',),
            ),
        )
    )

    validate_users_navigation_profiles(definition, _profiles())


def test_users_catalog_validation_rejects_unknown_or_full_access_profiles() -> None:
    for profile_key in ('unknown', 'local', 'administrator'):
        definition = NavigationDefinition(
            links=(
                NavigationLinkDefinition(
                    key=f'link-{profile_key}',
                    label='Link',
                    href='/link',
                    allowed_profiles=(profile_key,),
                ),
            )
        )

        with pytest.raises(WebDefinitionError, match='Users profile catalog'):
            validate_users_navigation_profiles(definition, _profiles())
