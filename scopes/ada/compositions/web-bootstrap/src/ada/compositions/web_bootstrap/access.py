from __future__ import annotations

from dataclasses import dataclass, replace

from atlanticus.web.environment import WebEnvironment
from atlanticus.web.identity.app_service import create_app_service_identity_provider
from atlanticus.web.identity.local import create_local_identity_provider
from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.identity.provider import IdentityProvider
from atlanticus.web.users.cosmos import (
    CosmosProfileCatalog,
    CosmosUsersGatewayAdapter,
    UsersCosmosProfileCache,
    UsersCosmosSource,
)
from atlanticus.web.users.local import create_local_users_source
from atlanticus.web.users.models import ResolvedUserRecord
from atlanticus.web.users.profiles import ADMINISTRATOR_PROFILE_KEY, ProfileCatalog
from atlanticus.web.users.source import UsersSource


@dataclass(frozen=True, slots=True)
class AdaAccessComponents:
    identity_provider: IdentityProvider
    users_source: UsersSource
    profiles: ProfileCatalog


class BootstrapAdminUsersSource(UsersSource):
    def __init__(self, *, source: UsersSource, principal_email: str) -> None:
        self._source = source
        self._principal_email = principal_email.casefold()

    def resolve(self, identity: AuthenticatedIdentity) -> ResolvedUserRecord | None:
        record = self._source.resolve(identity)
        if record is None or identity.email is None:
            return record
        if identity.email.casefold() != self._principal_email:
            return record
        if record.profile_key == ADMINISTRATOR_PROFILE_KEY:
            return record
        return replace(record, profile_key=ADMINISTRATOR_PROFILE_KEY)


def create_ada_access_components(
    *,
    environment: WebEnvironment,
    users_client,
    bootstrap_admin_principal: str | None = None,
) -> AdaAccessComponents:
    if not isinstance(environment, WebEnvironment):
        raise TypeError('environment must be WebEnvironment')

    users_gateway = CosmosUsersGatewayAdapter(client=users_client)
    profile_cache = UsersCosmosProfileCache(users_gateway)
    profiles = CosmosProfileCatalog(profile_cache)

    if environment.is_local:
        return AdaAccessComponents(
            identity_provider=create_local_identity_provider(),
            users_source=create_local_users_source(),
            profiles=profiles,
        )

    users_source: UsersSource = UsersCosmosSource(gateway=users_gateway, profiles=profile_cache)
    if bootstrap_admin_principal is not None:
        users_source = BootstrapAdminUsersSource(
            source=users_source,
            principal_email=bootstrap_admin_principal,
        )
    return AdaAccessComponents(
        identity_provider=create_app_service_identity_provider(),
        users_source=users_source,
        profiles=profiles,
    )
