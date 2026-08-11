from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from atlanticus.web.errors import WebDefinitionError

_KEY_PATTERN = re.compile(r'^[a-z0-9][a-z0-9._-]*$')


@dataclass(frozen=True, slots=True)
class NavigationUser:
    display_name: str
    profile: str
    initials: str
    email: str | None = None
    avatar_src: str | None = None

    def __post_init__(self) -> None:
        if not self.display_name.strip():
            raise WebDefinitionError('Navigation user display name must not be empty')
        if not self.profile.strip():
            raise WebDefinitionError('Navigation user profile must not be empty')
        if not self.initials.strip() or len(self.initials.strip()) > 4:
            raise WebDefinitionError(
                'Navigation user initials must contain between 1 and 4 characters'
            )
        if self.email is not None and not self.email.strip():
            raise WebDefinitionError('Navigation user email must not be empty when provided')
        if self.avatar_src is not None and not self.avatar_src.strip():
            raise WebDefinitionError(
                'Navigation user avatar source must not be empty when provided'
            )


@dataclass(frozen=True, slots=True)
class NavigationLink:
    key: str
    label: str
    href: str
    order: int = 0
    icon: str | None = None
    enabled: bool = True
    new_tab: bool = False
    force_reload: bool = False

    def __post_init__(self) -> None:
        _validate_key(self.key, label='Navigation link key')
        if not self.label.strip():
            raise WebDefinitionError('Navigation link label must not be empty')
        _validate_href(self.href)
        if self.icon is not None and not self.icon.strip():
            raise WebDefinitionError('Navigation link icon must not be empty when provided')

    @property
    def is_external(self) -> bool:
        return not self.href.startswith('/')


@dataclass(frozen=True, slots=True)
class NavigationGroup:
    key: str
    label: str
    links: tuple[NavigationLink, ...]
    order: int = 0
    icon: str | None = None
    enabled: bool = True
    expanded: bool = False

    def __post_init__(self) -> None:
        _validate_key(self.key, label='Navigation group key')
        if not self.label.strip():
            raise WebDefinitionError('Navigation group label must not be empty')
        if not self.links:
            raise WebDefinitionError('Navigation group must contain at least one link')
        if self.icon is not None and not self.icon.strip():
            raise WebDefinitionError('Navigation group icon must not be empty when provided')

        link_keys = [link.key for link in self.links]
        if len(link_keys) != len(set(link_keys)):
            raise WebDefinitionError(f'Navigation group contains duplicated link keys: {self.key}')


@dataclass(frozen=True, slots=True)
class NavigationMenu:
    user: NavigationUser
    links: tuple[NavigationLink, ...] = ()
    groups: tuple[NavigationGroup, ...] = ()

    def __post_init__(self) -> None:
        group_keys = [group.key for group in self.groups]
        if len(group_keys) != len(set(group_keys)):
            raise WebDefinitionError('Navigation menu contains duplicated group keys')

        link_keys = [link.key for link in self.links]
        link_keys.extend(link.key for group in self.groups for link in group.links)
        if len(link_keys) != len(set(link_keys)):
            raise WebDefinitionError('Navigation menu contains duplicated link keys')


def _validate_key(value: str, *, label: str) -> None:
    if not _KEY_PATTERN.fullmatch(value):
        raise WebDefinitionError(f'{label} has an invalid format')


def _validate_href(value: str) -> None:
    if value.startswith('/') and not value.startswith('//'):
        return

    parsed = urlparse(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise WebDefinitionError('Navigation link href must be an absolute path or HTTP(S) URL')
