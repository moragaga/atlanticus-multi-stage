# Espejo pedagógico: esta composición traduce EffectiveUser a NavigationPrincipal.
# La dependencia entre Users y Navigation vive aquí y no en ninguno de los dos módulos base.
from __future__ import annotations

from atlanticus.web.errors import WebDefinitionError
from atlanticus.web.identity.access import AccessRuntime
from atlanticus.web.navigation.api import (
    NavigationDefinition,
    NavigationPrincipal,
    NavigationPrincipalProvider,
    NavigationUser,
)
from atlanticus.web.users.models import EffectiveUser
from atlanticus.web.users.profiles import ProfileCatalog
from atlanticus.web.users.runtime import UsersRuntime


def create_users_navigation_principal_provider(
    *,
    access_runtime: AccessRuntime,
    users_runtime: UsersRuntime,
) -> NavigationPrincipalProvider:
    return NavigationPrincipalProvider(
        lambda: principal_from_effective_user(
            users_runtime.current(access_runtime.current())
        )
    )


def principal_from_effective_user(user: EffectiveUser) -> NavigationPrincipal:
    return NavigationPrincipal(
        access_key=user.profile.key,
        unrestricted=user.has_full_access,
        user=NavigationUser(
            display_name=user.display_name,
            email=user.email,
            profile_key=user.profile.key,
            profile_label=user.profile.label,
            profile_background_color=user.profile.background_color,
            profile_text_color=user.profile.text_color,
            avatar_text=user.avatar_text,
            avatar_background_color=user.avatar_background_color,
            avatar_text_color=user.avatar_text_color,
        ),
    )


def validate_users_navigation_profiles(
    definition: NavigationDefinition,
    profiles: ProfileCatalog,
) -> None:
    selectable = {profile.key for profile in profiles.restricted_access_profiles()}
    for key in definition.configured_profiles():
        if key not in selectable:
            raise WebDefinitionError(
                f'Navigation profile {key!r} is not available in the Users profile catalog'
            )
