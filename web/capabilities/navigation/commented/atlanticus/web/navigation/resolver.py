# Espejo pedagógico del módulo productivo.
# Los comentarios explican responsabilidades sin alterar estructura ni comportamiento.
from __future__ import annotations

from atlanticus.web.errors import WebDefinitionError
from atlanticus.web.identity.access import ACCESS_RUNTIME_SERVICE_KEY, AccessRuntime
from atlanticus.web.navigation.models import (
    NavigationDefinition,
    NavigationGroup,
    NavigationGroupDefinition,
    NavigationLinkDefinition,
    NavigationMenu,
    NavigationUser,
)
from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.models import EffectiveUser
from atlanticus.web.users.module import PROFILE_CATALOG_SERVICE_KEY
from atlanticus.web.users.profiles import ProfileCatalog, profile_has_access
from atlanticus.web.users.runtime import USERS_RUNTIME_SERVICE_KEY, UsersRuntime

NAVIGATION_DEFINITION_SERVICE_KEY = 'atlanticus.web.navigation.definition'


# Encapsula la operación resolve navigation para mantener esta responsabilidad aislada.
def resolve_navigation(
    definition: NavigationDefinition,
    *,
    user: EffectiveUser,
    profiles: ProfileCatalog,
) -> NavigationMenu:
    _validate_profiles(definition, profiles)
    links = tuple(
        link.to_resolved()
        for link in sorted(definition.links, key=_link_sort_key)
        if _can_open(link.effective_profiles(None), user)
    )
    groups: list[NavigationGroup] = []
    for group in sorted(definition.groups, key=_group_sort_key):
        children = tuple(
            link.to_resolved()
            for link in sorted(group.links, key=_link_sort_key)
            if _can_open(link.effective_profiles(group), user)
        )
        if children:
            groups.append(group.to_resolved(links=children))
    return NavigationMenu(
        user=_navigation_user(user),
        links=links,
        groups=tuple(groups),
    )


# Encapsula la operación resolve navigation from services para mantener esta responsabilidad aislada.
def resolve_navigation_from_services(services: ServiceRegistry) -> NavigationMenu:
    access = services.require(ACCESS_RUNTIME_SERVICE_KEY, AccessRuntime).current()
    user = services.require(USERS_RUNTIME_SERVICE_KEY, UsersRuntime).current(access)
    profiles = services.require(PROFILE_CATALOG_SERVICE_KEY, ProfileCatalog)
    definition = services.require(NAVIGATION_DEFINITION_SERVICE_KEY, NavigationDefinition)
    return resolve_navigation(definition, user=user, profiles=profiles)


# Encapsula la operación validate navigation definition para mantener esta responsabilidad aislada.
def validate_navigation_definition(
    definition: NavigationDefinition,
    profiles: ProfileCatalog,
) -> None:
    _validate_profiles(definition, profiles)


# Encapsula la operación validate profiles para mantener esta responsabilidad aislada.
def _validate_profiles(definition: NavigationDefinition, profiles: ProfileCatalog) -> None:
    selectable = {profile.key for profile in profiles.navigation_selectable()}
    for key in _iter_allowed_profiles(definition):
        if key not in selectable:
            raise WebDefinitionError(f'Navigation profile {key!r} is not available for selection')


# Encapsula la operación iter allowed profiles para mantener esta responsabilidad aislada.
def _iter_allowed_profiles(definition: NavigationDefinition):
    for link in definition.links:
        if link.allowed_profiles is not None:
            yield from link.allowed_profiles
    for group in definition.groups:
        yield from group.allowed_profiles
        for link in group.links:
            if link.allowed_profiles is not None:
                yield from link.allowed_profiles


# Encapsula la operación can open para mantener esta responsabilidad aislada.
def _can_open(allowed_profiles: tuple[str, ...], user: EffectiveUser) -> bool:
    return profile_has_access(user.profile.key, allowed_profiles)


# Encapsula la operación navigation user para mantener esta responsabilidad aislada.
def _navigation_user(user: EffectiveUser) -> NavigationUser:
    return NavigationUser(
        display_name=user.display_name,
        email=user.email,
        profile_key=user.profile.key,
        profile_label=user.profile.label,
        profile_background_color=user.profile.background_color,
        profile_text_color=user.profile.text_color,
        avatar_text=user.avatar_text,
        avatar_background_color=user.avatar_background_color,
        avatar_text_color=user.avatar_text_color,
    )


# Encapsula la operación link sort key para mantener esta responsabilidad aislada.
def _link_sort_key(link: NavigationLinkDefinition) -> tuple[int, str, str]:
    return (link.order, link.label, link.key)


# Encapsula la operación group sort key para mantener esta responsabilidad aislada.
def _group_sort_key(group: NavigationGroupDefinition) -> tuple[int, str, str]:
    return (group.order, group.label, group.key)
