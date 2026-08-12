from __future__ import annotations

from typing import Protocol

from atlanticus.web.users.cosmos.models import (
    ProfileCatalogDocument,
    UserDocument,
    UserLookupDocument,
    UsersStateDocument,
)


# Frontera privada del adapter. Connectivity implementará estas operaciones cuando cierre su API.
class UsersCosmosGateway(Protocol):
    def read_state(self) -> UsersStateDocument | None: ...

    def read_profile_catalog(self) -> ProfileCatalogDocument | None: ...

    def read_user(self, user_id: str) -> UserDocument | None: ...

    def read_identity_lookup(self, lookup_key: str) -> UserLookupDocument | None: ...

    def read_email_lookup(self, lookup_key: str) -> UserLookupDocument | None: ...

    def create_user_if_absent(self, document: UserDocument) -> UserDocument: ...

    def create_lookup_if_absent(self, document: UserLookupDocument) -> UserLookupDocument: ...
