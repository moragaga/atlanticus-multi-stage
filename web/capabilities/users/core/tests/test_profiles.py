import pytest

from atlanticus.web.users.errors import UsersDefinitionError
from atlanticus.web.users.profiles import (
    ADMINISTRATOR_PROFILE_KEY,
    DEFAULT_ADMINISTRATOR_COLOR,
    DEFAULT_GUEST_COLOR,
    GUEST_PROFILE_KEY,
    LOCAL_PROFILE_COLOR,
    LOCAL_PROFILE_KEY,
    ProfileCatalog,
    ProfileDefinition,
    profile_has_access,
)


def test_system_profiles_have_fixed_contracts_and_administrator_color_is_configurable() -> None:
    default = ProfileCatalog()
    changed = ProfileCatalog(administrator_color='#112233')

    assert tuple(profile.key for profile in default.all()) == (
        'local',
        'administrator',
        'guest',
    )
    assert default.require(LOCAL_PROFILE_KEY).color == LOCAL_PROFILE_COLOR
    assert default.require(ADMINISTRATOR_PROFILE_KEY).color == DEFAULT_ADMINISTRATOR_COLOR
    assert default.require(GUEST_PROFILE_KEY).color == DEFAULT_GUEST_COLOR
    assert changed.require(ADMINISTRATOR_PROFILE_KEY).label == 'Administrador'
    assert changed.require(ADMINISTRATOR_PROFILE_KEY).color == '#112233'
    assert changed.require(LOCAL_PROFILE_KEY).color == LOCAL_PROFILE_COLOR
    assert changed.require(GUEST_PROFILE_KEY).color == DEFAULT_GUEST_COLOR


def test_system_profiles_cannot_be_redefined_as_custom_profiles() -> None:
    with pytest.raises(UsersDefinitionError, match='cannot be redefined'):
        ProfileCatalog(
            custom_profiles=(
                ProfileDefinition(
                    key='administrator',
                    label='Owner',
                    color='#000000',
                ),
            )
        )


def test_only_administrator_and_custom_profiles_are_assignable() -> None:
    catalog = ProfileCatalog(
        custom_profiles=(
            ProfileDefinition(key='operator', label='Operador', color='#123456'),
        )
    )

    assert tuple(profile.key for profile in catalog.assignable()) == (
        'administrator',
        'operator',
    )
    assert tuple(profile.key for profile in catalog.navigation_selectable()) == (
        'guest',
        'operator',
    )


def test_profile_access_policy_keeps_system_full_access_implicit() -> None:
    assert profile_has_access('local', ()) is True
    assert profile_has_access('administrator', ()) is True
    assert profile_has_access('guest', ()) is False
    assert profile_has_access('operator', ('operator',)) is True
    assert profile_has_access('operator', ('viewer',)) is False


def test_guest_color_is_configurable_and_guest_is_navigation_selectable() -> None:
    catalog = ProfileCatalog(guest_color='#123456')

    assert catalog.require('guest').color == '#123456'
    assert [profile.key for profile in catalog.navigation_selectable()] == ['guest']
