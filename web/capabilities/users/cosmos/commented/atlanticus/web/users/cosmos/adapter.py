from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol, TypeVar

from atlanticus.web.users.cosmos.errors import UsersCosmosGatewayError
from atlanticus.web.users.cosmos.gateway import UsersCosmosGateway
from atlanticus.web.users.cosmos.keys import user_partition_key
from atlanticus.web.users.cosmos.models import (
    ProfileCatalogDocument,
    UserDocument,
    UserLookupDocument,
    UsersStateDocument,
)
from atlanticus.web.users.profiles import ProfileDefinition

T = TypeVar('T')


# Este protocolo replica únicamente la parte del CosmosClient estable que Users necesita.
class CosmosUsersClient(Protocol):
    def find_item(
        self,
        *,
        container_name: str,
        item_id: str,
        partition_key: object,
        include_metadata: bool = False,
    ) -> dict[str, Any] | None: ...

    def create_item(
        self,
        *,
        container_name: str,
        item: Mapping[str, Any],
        include_metadata: bool = False,
    ) -> dict[str, Any]: ...


# El adaptador traduce Cosmos a documentos Users sin resolver configuración ni lifecycle.
class CosmosUsersGatewayAdapter(UsersCosmosGateway):
    def __init__(
        self,
        *,
        client: CosmosUsersClient,
        users_container: str = 'users',
        support_container: str = 'users_support',
    ) -> None:
        self._client = client
        self._users_container = _container_name(users_container)
        self._support_container = _container_name(support_container)

    def read_state(self) -> UsersStateDocument | None:
        document = self._find_item(
            container_name=self._support_container,
            item_id='users',
            partition_key='system',
        )
        return self._parse_optional(document, _state_from_item)

    def read_profile_catalog(self) -> ProfileCatalogDocument | None:
        document = self._find_item(
            container_name=self._support_container,
            item_id='catalog',
            partition_key='profiles',
        )
        return self._parse_optional(document, _profile_catalog_from_item)

    def read_user(self, user_id: str) -> UserDocument | None:
        document = self._find_item(
            container_name=self._users_container,
            item_id='user',
            partition_key=user_partition_key(user_id),
        )
        return self._parse_optional(document, _user_from_item)

    def read_identity_lookup(self, lookup_key: str) -> UserLookupDocument | None:
        return self._read_lookup(kind='identity', lookup_key=lookup_key)

    def read_email_lookup(self, lookup_key: str) -> UserLookupDocument | None:
        return self._read_lookup(kind='email', lookup_key=lookup_key)

    def create_user_if_absent(self, document: UserDocument) -> UserDocument:
        item = _user_to_item(document)
        created = self._create_or_read(
            container_name=self._users_container,
            item=item,
        )
        return self._parse(created, _user_from_item)

    def create_lookup_if_absent(self, document: UserLookupDocument) -> UserLookupDocument:
        item = _lookup_to_item(document)
        created = self._create_or_read(
            container_name=self._users_container,
            item=item,
        )
        return self._parse(created, _lookup_from_item)

    def _read_lookup(self, *, kind: str, lookup_key: str) -> UserLookupDocument | None:
        document = self._find_item(
            container_name=self._users_container,
            item_id=kind,
            partition_key=lookup_key,
        )
        return self._parse_optional(document, _lookup_from_item)

    def _find_item(
        self,
        *,
        container_name: str,
        item_id: str,
        partition_key: object,
    ) -> dict[str, Any] | None:
        try:
            return self._client.find_item(
                container_name=container_name,
                item_id=item_id,
                partition_key=partition_key,
            )
        except Exception as error:
            raise UsersCosmosGatewayError('Could not read Cosmos users document') from error

    # create_item mantiene la creación condicional. Ante una carrera se relee el ganador.
    def _create_or_read(
        self,
        *,
        container_name: str,
        item: Mapping[str, Any],
    ) -> dict[str, Any]:
        try:
            return self._client.create_item(
                container_name=container_name,
                item=item,
            )
        except Exception as create_error:
            try:
                current = self._client.find_item(
                    container_name=container_name,
                    item_id=str(item['id']),
                    partition_key=item['partition_key'],
                )
            except Exception as read_error:
                raise UsersCosmosGatewayError(
                    'Could not resolve Cosmos users create conflict'
                ) from read_error
            if current is None:
                raise UsersCosmosGatewayError('Could not create Cosmos users document') from (
                    create_error
                )
            return current

    @staticmethod
    def _parse(document: Mapping[str, Any], parser: Callable[[Mapping[str, Any]], T]) -> T:
        try:
            return parser(document)
        except Exception as error:
            raise UsersCosmosGatewayError('Cosmos users document is invalid') from error

    @classmethod
    def _parse_optional(
        cls,
        document: Mapping[str, Any] | None,
        parser: Callable[[Mapping[str, Any]], T],
    ) -> T | None:
        if document is None:
            return None
        return cls._parse(document, parser)


def _state_from_item(item: Mapping[str, Any]) -> UsersStateDocument:
    return UsersStateDocument(
        source_revision=item['source_revision'],
        projection_status=item['projection_status'],
        projection_revision=item.get('projection_revision'),
        projected_by=item.get('projected_by'),
        projected_at_utc=item.get('projected_at_utc'),
        schema_version=item['schema_version'],
        id=item['id'],
        partition_key=item['partition_key'],
        type=item['type'],
    )


def _profile_catalog_from_item(item: Mapping[str, Any]) -> ProfileCatalogDocument:
    custom_profiles = item.get('custom_profiles', ())
    if not isinstance(custom_profiles, list | tuple):
        raise TypeError('custom_profiles must be a list or tuple')
    return ProfileCatalogDocument(
        source_revision=item['source_revision'],
        administrator_background_color=item['administrator_background_color'],
        administrator_text_color=item['administrator_text_color'],
        guest_background_color=item['guest_background_color'],
        guest_text_color=item['guest_text_color'],
        custom_profiles=tuple(_profile_from_item(profile) for profile in custom_profiles),
        schema_version=item['schema_version'],
        id=item['id'],
        partition_key=item['partition_key'],
        type=item['type'],
    )


def _profile_from_item(item: object) -> ProfileDefinition:
    if not isinstance(item, Mapping):
        raise TypeError('profile must be a mapping')
    return ProfileDefinition(
        key=item['key'],
        label=item['label'],
        background_color=item['background_color'],
        text_color=item['text_color'],
    )


def _user_from_item(item: Mapping[str, Any]) -> UserDocument:
    return UserDocument(
        user_id=item['user_id'],
        display_name=item['display_name'],
        profile_key=item['profile_key'],
        enabled=item['enabled'],
        pending=item['pending'],
        origin=item['origin'],
        issuer=item.get('issuer'),
        subject_id=item.get('subject_id'),
        email=item.get('email'),
        email_normalized=item.get('email_normalized'),
        source_revision=item.get('source_revision'),
        schema_version=item['schema_version'],
        id=item['id'],
        partition_key=item['partition_key'],
        type=item['type'],
    )


def _lookup_from_item(item: Mapping[str, Any]) -> UserLookupDocument:
    return UserLookupDocument(
        kind=item['kind'],
        lookup_key=item['lookup_key'],
        user_id=item['user_id'],
        schema_version=item['schema_version'],
        id=item['id'],
        partition_key=item['partition_key'],
        type=item['type'],
    )


def _user_to_item(document: UserDocument) -> dict[str, object]:
    return {
        'id': document.id,
        'partition_key': document.partition_key,
        'type': document.type,
        'schema_version': document.schema_version,
        'user_id': document.user_id,
        'issuer': document.issuer,
        'subject_id': document.subject_id,
        'display_name': document.display_name,
        'email': document.email,
        'email_normalized': document.email_normalized,
        'profile_key': document.profile_key,
        'enabled': document.enabled,
        'pending': document.pending,
        'origin': document.origin,
        'source_revision': document.source_revision,
    }


def _lookup_to_item(document: UserLookupDocument) -> dict[str, object]:
    return {
        'id': document.id,
        'partition_key': document.partition_key,
        'type': document.type,
        'schema_version': document.schema_version,
        'kind': document.kind,
        'lookup_key': document.lookup_key,
        'user_id': document.user_id,
    }


def _container_name(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Cosmos users container name must not be empty')
    if value != value.strip():
        raise ValueError('Cosmos users container name must not contain surrounding whitespace')
    return value
