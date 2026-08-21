# Este espejo pedagógico conserva exactamente el comportamiento del código productivo.
# Los comentarios explican la responsabilidad de composición sin alterar el AST.
from __future__ import annotations

from atlanticus.web.identity.access import ACCESS_RUNTIME_SERVICE_KEY, AccessRuntime
from atlanticus.web.identity.errors import AccessContextError
from atlanticus.web.manager import ManagerPrincipal
from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.models import EffectiveUser
from atlanticus.web.users.runtime import USERS_RUNTIME_SERVICE_KEY, UsersRuntime

_LAYOUT_PRINCIPAL = ManagerPrincipal(
    subject_id='manager-layout',
    display_name='Manager',
)


class EffectiveUserManagerPrincipalProvider:
    def __init__(self) -> None:
        self._services: ServiceRegistry | None = None

    def bind(self, services: ServiceRegistry) -> None:
        if not isinstance(services, ServiceRegistry):
            raise TypeError('services must be ServiceRegistry')
        if self._services is not None and self._services is not services:
            raise RuntimeError('Manager principal provider is already bound')
        self._services = services

    def __call__(self) -> ManagerPrincipal:
        services = self._services
        if services is None:
            return _LAYOUT_PRINCIPAL
        try:
            access = services.require(ACCESS_RUNTIME_SERVICE_KEY, AccessRuntime).current()
        except AccessContextError:
            return _LAYOUT_PRINCIPAL
        user = services.require(USERS_RUNTIME_SERVICE_KEY, UsersRuntime).current(access)
        return manager_principal_from_effective_user(user)


def manager_principal_from_effective_user(user: EffectiveUser) -> ManagerPrincipal:
    if not isinstance(user, EffectiveUser):
        raise TypeError('user must be EffectiveUser')
    return ManagerPrincipal(
        subject_id=user.subject_id,
        display_name=user.display_name,
        profile_keys=(user.profile.key,),
        is_local=user.is_local,
    )


def create_manager_principal_binding_module(
    provider: EffectiveUserManagerPrincipalProvider,
) -> WebModule:
    if not isinstance(provider, EffectiveUserManagerPrincipalProvider):
        raise TypeError('provider must be EffectiveUserManagerPrincipalProvider')
    return WebModule(
        name='ada-configuration-manager-principal',
        register_services=provider.bind,
    )
