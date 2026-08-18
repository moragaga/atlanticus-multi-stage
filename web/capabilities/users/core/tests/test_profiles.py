import pytest

from atlanticus.web.users.errors import UsersDefinitionError
from atlanticus.web.users.profiles import (
    ADMINISTRATOR_PROFILE_KEY,
    DEFAULT_ADMINISTRATOR_BACKGROUND_COLOR,
    DEFAULT_ADMINISTRATOR_TEXT_COLOR,
    DEFAULT_GUEST_BACKGROUND_COLOR,
    DEFAULT_GUEST_TEXT_COLOR,
    GUEST_PROFILE_KEY,
    LOCAL_PROFILE_BACKGROUND_COLOR,
    LOCAL_PROFILE_KEY,
    LOCAL_PROFILE_TEXT_COLOR,
    ProfileCatalog,
    ProfileDefinition,
    profile_has_access,
)


def test_system_profiles_have_fixed_contracts_and_configurable_visuals() -> None:
    default = ProfileCatalog()
    changed = ProfileCatalog(
        administrator_background_color='#112233',
        administrator_text_color='#AABBCC',
    )

    assert tuple(profile.key for profile in default.all()) == (
        'local',
        'administrator',
        'guest',
    )
    assert default.require(LOCAL_PROFILE_KEY).background_color == LOCAL_PROFILE_BACKGROUND_COLOR
    assert default.require(LOCAL_PROFILE_KEY).text_color == LOCAL_PROFILE_TEXT_COLOR
    assert (
        default.require(ADMINISTRATOR_PROFILE_KEY).background_color
        == DEFAULT_ADMINISTRATOR_BACKGROUND_COLOR
    )
    assert (
        default.require(ADMINISTRATOR_PROFILE_KEY).text_color
        == DEFAULT_ADMINISTRATOR_TEXT_COLOR
    )
    assert default.require(GUEST_PROFILE_KEY).background_color == DEFAULT_GUEST_BACKGROUND_COLOR
    assert default.require(GUEST_PROFILE_KEY).text_color == DEFAULT_GUEST_TEXT_COLOR
    assert changed.require(ADMINISTRATOR_PROFILE_KEY).label == 'Administrador'
    assert changed.require(ADMINISTRATOR_PROFILE_KEY).background_color == '#112233'
    assert changed.require(ADMINISTRATOR_PROFILE_KEY).text_color == '#AABBCC'


def test_system_profiles_cannot_be_redefined_as_custom_profiles() -> None:
    with pytest.raises(UsersDefinitionError, match='cannot be redefined'):
        ProfileCatalog(
            custom_profiles=(
                ProfileDefinition(
                    key='administrator',
                    label='Owner',
                    background_color='#000000',
                    text_color='#FFFFFF',
                ),
            )
        )


def test_only_administrator_and_custom_profiles_are_assignable() -> None:
    catalog = ProfileCatalog(
        custom_profiles=(
            ProfileDefinition(
                key='operator',
                label='Operador',
                background_color='#123456',
                text_color='#FFFFFF',
            ),
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


def test_guest_visuals_are_configurable_and_guest_is_navigation_selectable() -> None:
    catalog = ProfileCatalog(
        guest_background_color='#123456',
        guest_text_color='#FEDCBA',
    )

    assert catalog.require('guest').background_color == '#123456'
    assert catalog.require('guest').text_color == '#FEDCBA'
    assert [profile.key for profile in catalog.navigation_selectable()] == ['guest']
