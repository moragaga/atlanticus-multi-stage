from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from atlanticus.web.users.configuration.bundle import UsersConfigurationBundle
from atlanticus.web.users.configuration.errors import UsersConfigurationProjectionError
from atlanticus.web.users.configuration.models import DiscoveredUser
from atlanticus.web.users.configuration.projection import UsersProjectionState
from atlanticus.web.users.cosmos.keys import (
    email_lookup_key,
    identity_lookup_key,
)
from atlanticus.web.users.cosmos.models import (
    ProfileCatalogDocument,
    UserDocument,
    UserLookupDocument,
)


class CosmosUsersConfigurationClient(Protocol):
    def health_check(self) -> bool: ...

    def find_item(
        self,
        *,
        container_name: str,
        item_id: str,
        partition_key: object,
    ) -> dict[str, Any] | None: ...

    def upsert_item(
        self,
        *,
        container_name: str,
        item: dict[str, Any],
    ) -> dict[str, Any]: ...

    def query_items(
        self,
        *,
        container_name: str,
        query: str,
        parameters: list[dict[str, object]],
    ) -> list[dict[str, Any]]: ...


@dataclass(frozen=True, slots=True)
class CosmosUsersConfigurationSettings:
    users_container: str = 'users'
    support_container: str = 'users_support'


class CosmosUsersProjectionRepository:
    def __init__(
        self,
        *,
        client: CosmosUsersConfigurationClient,
        settings: CosmosUsersConfigurationSettings = CosmosUsersConfigurationSettings(),
    ) -> None:
        self._client = client
        self._settings = settings

    def load_state(self) -> UsersProjectionState | None:
        try:
            document = self._client.find_item(
                container_name=self._settings.support_container,
                item_id='users',
                partition_key='system',
            )
        except Exception as error:
            raise UsersConfigurationProjectionError(
                'Could not read Cosmos users projection state'
            ) from error
        if document is None or document.get('projection_status') != 'ready':
            return None
        try:
            return UsersProjectionState(
                revision=str(document['projection_revision']),
                source_revision=str(document['source_revision']),
                projected_by=str(document['projected_by']),
                projected_at_utc=datetime.fromisoformat(str(document['projected_at_utc'])),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise UsersConfigurationProjectionError(
                'Cosmos users projection state is invalid'
            ) from error

    def project(self, bundle: UsersConfigurationBundle, *, actor: str) -> UsersProjectionState:
        state = UsersProjectionState.create(
            source_revision=bundle.revision,
            projected_by=actor,
        )
        try:
            self._write_transition_state(bundle.revision)
            self._write_profile_catalog(bundle)
            configured_ids = {user.user_id for user in bundle.catalog.users}
            for user in bundle.catalog.users:
                self._write_user(bundle, user)
            self._disable_missing_projection_users(bundle, configured_ids)
            self._write_state(state)
        except UsersConfigurationProjectionError:
            raise
        except Exception as error:
            raise UsersConfigurationProjectionError(
                'Could not write Cosmos users projection'
            ) from error
        return state

    def health_check(self) -> bool:
        try:
            return bool(self._client.health_check())
        except Exception:
            return False


    def _write_transition_state(self, source_revision: str) -> None:
        self._client.upsert_item(
            container_name=self._settings.support_container,
            item={
                'id': 'users',
                'partition_key': 'system',
                'type': 'users_state',
                'schema_version': 1,
                'source_revision': source_revision,
                'projection_status': 'projecting',
                'projection_revision': None,
                'projected_by': None,
                'projected_at_utc': None,
            },
        )

    def _disable_missing_projection_users(
        self,
        bundle: UsersConfigurationBundle,
        configured_ids: set[str],
    ) -> None:
        documents = self._client.query_items(
            container_name=self._settings.users_container,
            query='SELECT * FROM c WHERE c.type = @type AND c.origin = @origin',
            parameters=[
                {'name': '@type', 'value': 'user'},
                {'name': '@origin', 'value': 'projection'},
            ],
        )
        for document in documents:
            user_id = str(document.get('user_id') or '')
            if not user_id or user_id in configured_ids:
                continue
            disabled = dict(document)
            disabled['enabled'] = False
            disabled['pending'] = False
            disabled['origin'] = 'projection'
            disabled['source_revision'] = bundle.revision
            self._client.upsert_item(
                container_name=self._settings.users_container,
                item=disabled,
            )

    def _write_profile_catalog(self, bundle: UsersConfigurationBundle) -> None:
        catalog = ProfileCatalogDocument(
            source_revision=bundle.revision,
            administrator_color=bundle.catalog.administrator_color,
            guest_color=bundle.catalog.guest_color,
            custom_profiles=tuple(
                profile.to_profile_definition() for profile in bundle.catalog.profiles
            ),
        )
        self._client.upsert_item(
            container_name=self._settings.support_container,
            item={
                'id': catalog.id,
                'partition_key': catalog.partition_key,
                'type': catalog.type,
                'schema_version': catalog.schema_version,
                'source_revision': catalog.source_revision,
                'administrator_color': catalog.administrator_color,
                'guest_color': catalog.guest_color,
                'custom_profiles': [
                    {'key': item.key, 'label': item.label, 'color': item.color}
                    for item in catalog.custom_profiles
                ],
            },
        )

    def _write_user(self, bundle: UsersConfigurationBundle, configuration) -> None:
        document = UserDocument(
            user_id=configuration.user_id,
            issuer=configuration.issuer,
            subject_id=configuration.subject_id,
            display_name=configuration.display_name,
            email=configuration.email,
            profile_key=configuration.profile_key,
            enabled=configuration.enabled,
            pending=False,
            origin='projection',
            source_revision=bundle.revision,
        )
        self._client.upsert_item(
            container_name=self._settings.users_container,
            item=_user_document(document),
        )
        self._client.upsert_item(
            container_name=self._settings.users_container,
            item=_lookup_document(
                UserLookupDocument(
                    kind='email',
                    lookup_key=email_lookup_key(configuration.email),
                    user_id=configuration.user_id,
                )
            ),
        )
        if configuration.issuer is not None and configuration.subject_id is not None:
            self._client.upsert_item(
                container_name=self._settings.users_container,
                item=_lookup_document(
                    UserLookupDocument(
                        kind='identity',
                        lookup_key=identity_lookup_key(
                            issuer=configuration.issuer,
                            subject_id=configuration.subject_id,
                        ),
                        user_id=configuration.user_id,
                    )
                ),
            )

    def _write_state(self, state: UsersProjectionState) -> None:
        self._client.upsert_item(
            container_name=self._settings.support_container,
            item={
                'id': 'users',
                'partition_key': 'system',
                'type': 'users_state',
                'schema_version': 1,
                'source_revision': state.source_revision,
                'projection_status': 'ready',
                'projection_revision': state.revision,
                'projected_by': state.projected_by,
                'projected_at_utc': state.projected_at_utc.isoformat(),
            },
        )


class CosmosDiscoveredUsersSource:
    def __init__(
        self,
        *,
        client: CosmosUsersConfigurationClient,
        settings: CosmosUsersConfigurationSettings = CosmosUsersConfigurationSettings(),
    ) -> None:
        self._client = client
        self._settings = settings

    def list_discovered(self) -> tuple[DiscoveredUser, ...]:
        try:
            documents = self._client.query_items(
                container_name=self._settings.users_container,
                query=(
                    'SELECT * FROM c WHERE c.type = @type '
                    'AND c.origin = @origin AND c.pending = true'
                ),
                parameters=[
                    {'name': '@type', 'value': 'user'},
                    {'name': '@origin', 'value': 'identity'},
                ],
            )
        except Exception as error:
            raise UsersConfigurationProjectionError(
                'Could not read discovered Cosmos users'
            ) from error
        result: list[DiscoveredUser] = []
        for document in documents:
            issuer = document.get('issuer')
            subject_id = document.get('subject_id')
            email = document.get('email')
            if not issuer or not subject_id or not email:
                continue
            result.append(
                DiscoveredUser(
                    user_id=str(document['user_id']),
                    issuer=str(issuer),
                    subject_id=str(subject_id),
                    display_name=str(document['display_name']),
                    email=str(email),
                )
            )
        return tuple(result)


def _user_document(document: UserDocument) -> dict[str, object]:
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


def _lookup_document(document: UserLookupDocument) -> dict[str, object]:
    return {
        'id': document.id,
        'partition_key': document.partition_key,
        'type': document.type,
        'schema_version': document.schema_version,
        'kind': document.kind,
        'lookup_key': document.lookup_key,
        'user_id': document.user_id,
    }
