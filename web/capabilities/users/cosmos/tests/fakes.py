from __future__ import annotations

from atlanticus.web.users.cosmos.gateway import UsersCosmosGateway
from atlanticus.web.users.cosmos.models import (
    ProfileCatalogDocument,
    UserDocument,
    UserLookupDocument,
    UsersStateDocument,
)


class FakeUsersCosmosGateway(UsersCosmosGateway):
    def __init__(
        self,
        *,
        state: UsersStateDocument | None,
        catalog: ProfileCatalogDocument | None,
        users: tuple[UserDocument, ...] = (),
        lookups: tuple[UserLookupDocument, ...] = (),
    ) -> None:
        self.state = state
        self.catalog = catalog
        self.users = {document.user_id: document for document in users}
        self.lookups = {document.lookup_key: document for document in lookups}
        self.state_reads = 0
        self.catalog_reads = 0

    def read_state(self) -> UsersStateDocument | None:
        self.state_reads += 1
        return self.state

    def read_profile_catalog(self) -> ProfileCatalogDocument | None:
        self.catalog_reads += 1
        return self.catalog

    def read_user(self, user_id: str) -> UserDocument | None:
        return self.users.get(user_id)

    def read_identity_lookup(self, lookup_key: str) -> UserLookupDocument | None:
        document = self.lookups.get(lookup_key)
        if document is None or document.kind != 'identity':
            return None
        return document

    def read_email_lookup(self, lookup_key: str) -> UserLookupDocument | None:
        document = self.lookups.get(lookup_key)
        if document is None or document.kind != 'email':
            return None
        return document

    def create_user_if_absent(self, document: UserDocument) -> UserDocument:
        existing = self.users.get(document.user_id)
        if existing is not None:
            return existing
        self.users[document.user_id] = document
        return document

    def create_lookup_if_absent(self, document: UserLookupDocument) -> UserLookupDocument:
        existing = self.lookups.get(document.lookup_key)
        if existing is not None:
            return existing
        self.lookups[document.lookup_key] = document
        return document
