from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from atlanticus.web.users.cosmos import CosmosUsersGatewayAdapter
from atlanticus.web.users.cosmos.errors import UsersCosmosGatewayError
from atlanticus.web.users.cosmos.keys import email_lookup_key, identity_lookup_key
from atlanticus.web.users.cosmos.models import UserDocument, UserLookupDocument


class ContractCosmosClient:
    def __init__(self) -> None:
        self.items: dict[tuple[str, object, str], dict[str, Any]] = {}
        self.find_calls: list[dict[str, object]] = []
        self.create_calls: list[dict[str, object]] = []
        self.fail_find = False

    def find_item(
        self,
        *,
        container_name: str,
        item_id: str,
        partition_key: object,
        include_metadata: bool = False,
    ) -> dict[str, Any] | None:
        self.find_calls.append(
            {
                'container_name': container_name,
                'item_id': item_id,
                'partition_key': partition_key,
                'include_metadata': include_metadata,
            }
        )
        if self.fail_find:
            raise RuntimeError('read failed')
        value = self.items.get((container_name, partition_key, item_id))
        return dict(value) if value is not None else None

    def create_item(
        self,
        *,
        container_name: str,
        item: Mapping[str, Any],
        include_metadata: bool = False,
    ) -> dict[str, Any]:
        document = dict(item)
        self.create_calls.append(
            {
                'container_name': container_name,
                'item': document,
                'include_metadata': include_metadata,
            }
        )
        key = (container_name, document['partition_key'], document['id'])
        if key in self.items:
            raise RuntimeError('conflict')
        self.items[key] = document
        return dict(document)


def _state_item() -> dict[str, object]:
    return {
        'id': 'users',
        'partition_key': 'system',
        'type': 'users_state',
        'schema_version': 2,
        'source_revision': 'revision-1',
        'projection_status': 'ready',
        'projection_revision': 'projection-1',
        'projected_by': 'administrator',
        'projected_at_utc': '2026-08-19T12:00:00+00:00',
    }


def _catalog_item() -> dict[str, object]:
    return {
        'id': 'catalog',
        'partition_key': 'profiles',
        'type': 'profile_catalog',
        'schema_version': 2,
        'source_revision': 'revision-1',
        'administrator_background_color': '#112233',
        'administrator_text_color': '#FFFFFF',
        'guest_background_color': '#445566',
        'guest_text_color': '#FFFFFF',
        'custom_profiles': [
            {
                'key': 'operator',
                'label': 'Operador',
                'background_color': '#778899',
                'text_color': '#FFFFFF',
            }
        ],
    }


def _user() -> UserDocument:
    return UserDocument(
        user_id='user-1',
        issuer='entra',
        subject_id='subject-1',
        display_name='User One',
        email='one@example.com',
        profile_key='operator',
        enabled=True,
        pending=False,
        origin='projection',
        source_revision='revision-1',
    )


def test_gateway_reads_users_documents_through_real_cosmos_contract() -> None:
    client = ContractCosmosClient()
    identity_key = identity_lookup_key(issuer='entra', subject_id='subject-1')
    email_key = email_lookup_key('one@example.com')
    client.items.update(
        {
            ('users_support', 'system', 'users'): _state_item(),
            ('users_support', 'profiles', 'catalog'): _catalog_item(),
            ('users', 'user:user-1', 'user'): {
                'id': 'user',
                'partition_key': 'user:user-1',
                'type': 'user',
                'schema_version': 2,
                'user_id': 'user-1',
                'issuer': 'entra',
                'subject_id': 'subject-1',
                'display_name': 'User One',
                'email': 'one@example.com',
                'email_normalized': 'one@example.com',
                'profile_key': 'operator',
                'enabled': True,
                'pending': False,
                'origin': 'projection',
                'source_revision': 'revision-1',
            },
            ('users', identity_key, 'identity'): {
                'id': 'identity',
                'partition_key': identity_key,
                'type': 'user_lookup',
                'schema_version': 2,
                'kind': 'identity',
                'lookup_key': identity_key,
                'user_id': 'user-1',
            },
            ('users', email_key, 'email'): {
                'id': 'email',
                'partition_key': email_key,
                'type': 'user_lookup',
                'schema_version': 2,
                'kind': 'email',
                'lookup_key': email_key,
                'user_id': 'user-1',
            },
        }
    )
    gateway = CosmosUsersGatewayAdapter(client=client)

    assert gateway.read_state().source_revision == 'revision-1'
    assert gateway.read_profile_catalog().custom_profiles[0].key == 'operator'
    assert gateway.read_user('user-1').email == 'one@example.com'
    assert gateway.read_identity_lookup(identity_key).user_id == 'user-1'
    assert gateway.read_email_lookup(email_key).user_id == 'user-1'

    assert [call['partition_key'] for call in client.find_calls] == [
        'system',
        'profiles',
        'user:user-1',
        identity_key,
        email_key,
    ]


def test_gateway_creates_users_and_lookups_with_create_item() -> None:
    client = ContractCosmosClient()
    gateway = CosmosUsersGatewayAdapter(client=client)
    user = _user()
    lookup = UserLookupDocument(
        kind='identity',
        lookup_key=identity_lookup_key(issuer='entra', subject_id='subject-1'),
        user_id=user.user_id,
    )

    created_user = gateway.create_user_if_absent(user)
    created_lookup = gateway.create_lookup_if_absent(lookup)

    assert created_user == user
    assert created_lookup == lookup
    assert client.create_calls[0]['container_name'] == 'users'
    assert client.create_calls[0]['item']['partition_key'] == 'user:user-1'
    assert client.create_calls[1]['item']['id'] == 'identity'
    assert client.create_calls[1]['item']['partition_key'] == lookup.lookup_key


def test_gateway_recovers_existing_document_after_create_conflict() -> None:
    client = ContractCosmosClient()
    user = _user()
    client.items[('users', user.partition_key, user.id)] = {
        'id': user.id,
        'partition_key': user.partition_key,
        'type': user.type,
        'schema_version': user.schema_version,
        'user_id': user.user_id,
        'issuer': user.issuer,
        'subject_id': user.subject_id,
        'display_name': user.display_name,
        'email': user.email,
        'email_normalized': user.email_normalized,
        'profile_key': user.profile_key,
        'enabled': user.enabled,
        'pending': user.pending,
        'origin': user.origin,
        'source_revision': user.source_revision,
    }
    gateway = CosmosUsersGatewayAdapter(client=client)

    actual = gateway.create_user_if_absent(user)

    assert actual == user
    assert client.find_calls[-1]['partition_key'] == 'user:user-1'


def test_gateway_wraps_transport_and_document_errors() -> None:
    client = ContractCosmosClient()
    gateway = CosmosUsersGatewayAdapter(client=client)
    client.fail_find = True

    with pytest.raises(UsersCosmosGatewayError, match='Could not read Cosmos users document'):
        gateway.read_state()

    client.fail_find = False
    client.items[('users_support', 'system', 'users')] = {'id': 'users'}

    with pytest.raises(UsersCosmosGatewayError, match='Cosmos users document is invalid'):
        gateway.read_state()
