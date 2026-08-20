# Espejo pedagógico: Users clasifica perfiles por semántica de acceso genérica.
# restricted_access_profiles no menciona Navigation y puede ser consumido por cualquier política externa.
from __future__ import annotations

from atlanticus.web.users.cosmos.errors import UsersCosmosGatewayError
from atlanticus.web.users.cosmos.gateway import UsersCosmosGateway
from atlanticus.web.users.cosmos.models import UsersStateDocument
from atlanticus.web.users.errors import UsersDefinitionError, UsersSourceUnavailableError
from atlanticus.web.users.profiles import ProfileCatalog, ProfileDefinition


class UsersCosmosProfileCache:
    def __init__(self, gateway: UsersCosmosGateway) -> None:
        self._gateway = gateway
        self._source_revision: str | None = None
        self._catalog: ProfileCatalog | None = None

    @property
    def source_revision(self) -> str | None:
        return self._source_revision

    def ensure_current(self) -> UsersStateDocument | None:
        try:
            state = self._gateway.read_state()
        except UsersCosmosGatewayError as error:
            raise UsersSourceUnavailableError('Users Cosmos state is unavailable') from error
        # Sin state todavía no existe una configuración materializada: los perfiles de sistema son suficientes.
        if state is None:
            self._catalog = ProfileCatalog()
            self._source_revision = None
            return None
        # Un state existente pero incompleto sigue siendo un error real y no se oculta con fallback.
        if state.projection_status != 'ready':
            raise UsersSourceUnavailableError('Users projection is not ready')
        if self._catalog is None or self._source_revision != state.source_revision:
            self._reload(state.source_revision)
        return state

    def current(self) -> ProfileCatalog:
        if self._catalog is None:
            self.ensure_current()
        if self._catalog is None:
            raise UsersSourceUnavailableError('Users profile catalog is unavailable')
        return self._catalog

    def _reload(self, source_revision: str) -> None:
        try:
            document = self._gateway.read_profile_catalog()
        except UsersCosmosGatewayError as error:
            raise UsersSourceUnavailableError('Users profile catalog is unavailable') from error
        if document is None or document.source_revision != source_revision:
            raise UsersSourceUnavailableError('Users profile catalog revision is not ready')
        try:
            catalog = ProfileCatalog(
                administrator_background_color=document.administrator_background_color,
                administrator_text_color=document.administrator_text_color,
                guest_background_color=document.guest_background_color,
                guest_text_color=document.guest_text_color,
                custom_profiles=document.custom_profiles,
            )
        except UsersDefinitionError as error:
            raise UsersSourceUnavailableError('Users profile catalog is invalid') from error
        self._catalog = catalog
        self._source_revision = source_revision


class CosmosProfileCatalog(ProfileCatalog):
    def __init__(self, cache: UsersCosmosProfileCache) -> None:
        super().__init__()
        self._cache = cache

    def require(self, key: str) -> ProfileDefinition:
        return self._cache.current().require(key)

    def all(self) -> tuple[ProfileDefinition, ...]:
        return self._cache.current().all()

    def assignable(self) -> tuple[ProfileDefinition, ...]:
        return self._cache.current().assignable()

    def restricted_access_profiles(self) -> tuple[ProfileDefinition, ...]:
        return self._cache.current().restricted_access_profiles()
