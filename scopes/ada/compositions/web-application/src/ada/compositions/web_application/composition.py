from __future__ import annotations

from atlanticus.web.compositions.navigation_activity import (
    create_navigation_activity_route_resolver,
)
from atlanticus.web.compositions.users_navigation import (
    create_users_navigation_module,
    validate_users_navigation_profiles,
)
from atlanticus.web.identity.access import ACCESS_RUNTIME_SERVICE_KEY, AccessRuntime
from atlanticus.web.identity.module import create_identity_module
from atlanticus.web.identity.provider import IdentityProvider
from atlanticus.web.models import ApplicationMetadata
from atlanticus.web.modules import WebModule
from atlanticus.web.navigation.api import (
    NavigationDefinitionProvider,
    create_navigation_authorization_module,
    create_navigation_module,
)
from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.activity import UserActivityRepository, create_user_activity_module
from atlanticus.web.users.models import EffectiveUser
from atlanticus.web.users.module import create_users_module
from atlanticus.web.users.profiles import ProfileCatalog
from atlanticus.web.users.resolver import UsersAccessResolver
from atlanticus.web.users.runtime import USERS_RUNTIME_SERVICE_KEY, UsersRuntime
from atlanticus.web.users.source import UsersSource


def create_ada_application_modules(
    *,
    metadata: ApplicationMetadata,
    identity_provider: IdentityProvider,
    users_source: UsersSource,
    users_runtime: UsersRuntime,
    profiles: ProfileCatalog,
    navigation_provider: NavigationDefinitionProvider | None = None,
    activity_repository: UserActivityRepository | None = None,
) -> tuple[WebModule, ...]:
    users_resolver = UsersAccessResolver(
        source=users_source,
        runtime=users_runtime,
        profiles=profiles,
    )
    modules: list[WebModule] = [
        create_users_module(users_runtime, profiles),
        create_identity_module(identity_provider, access_resolver=users_resolver),
    ]

    if navigation_provider is not None:
        validate_users_navigation_profiles(navigation_provider.current(), profiles)
        modules.extend(
            [
                create_navigation_module(definition_provider=navigation_provider),
                create_users_navigation_module(),
                create_navigation_authorization_module(),
            ]
        )

    if activity_repository is not None:
        modules.append(
            create_user_activity_module(
                repository=activity_repository,
                application_key=metadata.application_id,
                user_provider=_current_effective_user,
                route_resolver_factory=(
                    create_navigation_activity_route_resolver
                    if navigation_provider is not None
                    else None
                ),
            )
        )

    return tuple(modules)


def _current_effective_user(services: ServiceRegistry) -> EffectiveUser:
    access = services.require(ACCESS_RUNTIME_SERVICE_KEY, AccessRuntime).current()
    return services.require(USERS_RUNTIME_SERVICE_KEY, UsersRuntime).current(access)
