from __future__ import annotations

import re
from dataclasses import dataclass

from atlanticus.web.users.errors import UsersDefinitionError

LOCAL_PROFILE_KEY = 'local'
ADMINISTRATOR_PROFILE_KEY = 'administrator'
GUEST_PROFILE_KEY = 'guest'
LOCAL_PROFILE_COLOR = '#3778C2'
DEFAULT_ADMINISTRATOR_COLOR = '#673AB7'
GUEST_PROFILE_COLOR = '#FF5722'
_SYSTEM_PROFILE_KEYS = frozenset(
    {
        LOCAL_PROFILE_KEY,
        ADMINISTRATOR_PROFILE_KEY,
        GUEST_PROFILE_KEY,
    }
)
_HEX_COLOR = re.compile(r'^#[0-9A-Fa-f]{6}$')


@dataclass(frozen=True, slots=True)
class ProfileDefinition:
    key: str
    label: str
    color: str

    def __post_init__(self) -> None:
        key = _normalize_key(self.key)
        label = self.label.strip()
        color = self.color.strip().upper()
        if not label:
            raise UsersDefinitionError('Profile label must not be empty')
        if not _HEX_COLOR.fullmatch(color):
            raise UsersDefinitionError('Profile color must use #RRGGBB format')
        object.__setattr__(self, 'key', key)
        object.__setattr__(self, 'label', label)
        object.__setattr__(self, 'color', color)


class ProfileCatalog:
    def __init__(
        self,
        *,
        administrator_color: str = DEFAULT_ADMINISTRATOR_COLOR,
        custom_profiles: tuple[ProfileDefinition, ...] = (),
    ) -> None:
        administrator = ProfileDefinition(
            key=ADMINISTRATOR_PROFILE_KEY,
            label='Administrador',
            color=administrator_color,
        )
        system_profiles = (
            ProfileDefinition(
                key=LOCAL_PROFILE_KEY,
                label='Local',
                color=LOCAL_PROFILE_COLOR,
            ),
            administrator,
            ProfileDefinition(
                key=GUEST_PROFILE_KEY,
                label='Invitado',
                color=GUEST_PROFILE_COLOR,
            ),
        )
        profiles = {profile.key: profile for profile in system_profiles}
        for profile in custom_profiles:
            if profile.key in _SYSTEM_PROFILE_KEYS:
                raise UsersDefinitionError(
                    f'System profile {profile.key!r} cannot be redefined'
                )
            if profile.key in profiles:
                raise UsersDefinitionError(f'Duplicate profile key {profile.key!r}')
            profiles[profile.key] = profile
        self._profiles = profiles
        self._custom_keys = tuple(profile.key for profile in custom_profiles)

    def require(self, key: str) -> ProfileDefinition:
        normalized = _normalize_key(key)
        try:
            return self._profiles[normalized]
        except KeyError as error:
            raise UsersDefinitionError(f'Unknown profile {normalized!r}') from error

    def all(self) -> tuple[ProfileDefinition, ...]:
        return tuple(self._profiles.values())

    def assignable(self) -> tuple[ProfileDefinition, ...]:
        return (
            self._profiles[ADMINISTRATOR_PROFILE_KEY],
            *(self._profiles[key] for key in self._custom_keys),
        )

    def navigation_selectable(self) -> tuple[ProfileDefinition, ...]:
        return tuple(self._profiles[key] for key in self._custom_keys)


def has_full_access(profile_key: str) -> bool:
    return _normalize_key(profile_key) in {
        LOCAL_PROFILE_KEY,
        ADMINISTRATOR_PROFILE_KEY,
    }


def profile_has_access(profile_key: str, allowed_profiles: tuple[str, ...]) -> bool:
    normalized_profile = _normalize_key(profile_key)
    if has_full_access(normalized_profile):
        return True
    return normalized_profile in {_normalize_key(value) for value in allowed_profiles}


def _normalize_key(value: str) -> str:
    normalized = value.strip().casefold()
    if not normalized:
        raise UsersDefinitionError('Profile key must not be empty')
    if any(character.isspace() for character in normalized):
        raise UsersDefinitionError('Profile key must not contain spaces')
    return normalized
