from __future__ import annotations

from atlanticus.web.navigation.models import (
    NavigationDefinition,
    NavigationGroup,
    NavigationGroupDefinition,
    NavigationLinkDefinition,
    NavigationMenu,
    NavigationPrincipal,
)
from atlanticus.web.navigation.principal import (
    NAVIGATION_PRINCIPAL_PROVIDER_SERVICE_KEY,
    NavigationPrincipalProvider,
)
from atlanticus.web.services import ServiceRegistry

NAVIGATION_DEFINITION_SERVICE_KEY = 'atlanticus.web.navigation.definition'


# Resuelve `resolve navigation` manteniendo validación y estado explícitos.
def resolve_navigation(
    definition: NavigationDefinition,
    *,
    principal: NavigationPrincipal,
) -> NavigationMenu:
    links = tuple(
        link.to_resolved()
        for link in sorted(definition.links, key=_link_sort_key)
        if link.enabled and _can_open(link.effective_profiles(None), principal)
    )
    groups: list[NavigationGroup] = []
    for group in sorted(definition.groups, key=_group_sort_key):
        if not group.enabled:
            continue
        children = tuple(
            link.to_resolved()
            for link in sorted(group.links, key=_link_sort_key)
            if link.enabled and _can_open(link.effective_profiles(group), principal)
        )
        if children:
            groups.append(group.to_resolved(links=children))
    return NavigationMenu(
        user=principal.user,
        links=links,
        groups=tuple(groups),
    )


# Resuelve `resolve navigation from services` manteniendo validación y estado explícitos.
def resolve_navigation_from_services(services: ServiceRegistry) -> NavigationMenu:
    definition = services.require(NAVIGATION_DEFINITION_SERVICE_KEY, NavigationDefinition)
    provider = services.require(
        NAVIGATION_PRINCIPAL_PROVIDER_SERVICE_KEY,
        NavigationPrincipalProvider,
    )
    return resolve_navigation(definition, principal=provider.current())


# Resuelve `can open` manteniendo validación y estado explícitos.
def _can_open(
    allowed_profiles: tuple[str, ...],
    principal: NavigationPrincipal,
) -> bool:
    if principal.unrestricted:
        return True
    return principal.access_key in allowed_profiles


# Resuelve `link sort key` manteniendo validación y estado explícitos.
def _link_sort_key(link: NavigationLinkDefinition) -> tuple[int, str, str]:
    return (link.order, link.label, link.key)


# Resuelve `group sort key` manteniendo validación y estado explícitos.
def _group_sort_key(group: NavigationGroupDefinition) -> tuple[int, str, str]:
    return (group.order, group.label, group.key)
