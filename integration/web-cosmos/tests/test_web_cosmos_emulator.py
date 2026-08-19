from __future__ import annotations

import os
import time
import uuid
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pytest

from atlanticus.connectivity.cosmos import (
    CosmosClient,
    CosmosContainerSpec,
    CosmosPatchOperation,
    CosmosProvisioner,
    CosmosSettings,
)
from atlanticus.web.users.activity import (
    COSMOS_USER_ACTIVITY_RECORD_TYPE,
    COSMOS_USER_ACTIVITY_STORAGE_SCHEMA_VERSION,
    ActivityRouteIdentity,
    CosmosUserActivityRepository,
    Screen,
    UserActivityDocument,
    UserActivityEvent,
    UserActivityEventType,
    Viewport,
)
from atlanticus.web.users.activity.errors import UsersActivityConflictError
from atlanticus.web.users.activity.requirements import USER_ACTIVITY_COSMOS_REQUIREMENTS
from atlanticus.web.users.cosmos import (
    USERS_COSMOS_REQUIREMENTS,
    CosmosDiscoveredUsersSource,
    CosmosUsersGatewayAdapter,
)
from atlanticus.web.users.cosmos.keys import email_lookup_key, identity_lookup_key
from atlanticus.web.users.cosmos.models import UserDocument, UserLookupDocument
from atlanticus.web.users.models import EffectiveUser
from atlanticus.web.users.profiles import ProfileDefinition

pytestmark = pytest.mark.integration

_RUN = os.getenv('ATLANTICUS_RUN_WEB_COSMOS_INTEGRATION') == '1'
_READY_TIMEOUT_SECONDS = 120.0
_READY_INTERVAL_SECONDS = 1.0


@pytest.mark.skipif(not _RUN, reason='Web Cosmos emulator integration is disabled')
def test_web_users_and_activity_against_real_cosmos_contract() -> None:
    _wait_until_ready()
    database_name = os.environ.get('ATLANTICUS_WEB_COSMOS_DATABASE') or (
        f'atlanticus-web-it-{uuid.uuid4().hex[:8]}'
    )
    settings = CosmosSettings(
        endpoint=os.environ['ATLANTICUS_COSMOS_ENDPOINT'],
        key=os.environ['ATLANTICUS_COSMOS_KEY'],
        database_name=database_name,
        allow_insecure_http=True,
        max_query_items=100,
        page_size=50,
    )
    client = CosmosClient(settings=settings)
    try:
        _provision(client)
        suffix = uuid.uuid4().hex[:8]
        user = _exercise_users(client, suffix=suffix)
        activity = _exercise_activity(client, user=user, suffix=suffix)
        print(f'Cosmos database: {database_name}')
        print(f'Users partition: {user.partition_key}')
        print(f'Activity document: {activity.id}')
    finally:
        client.close()


def _provision(client: CosmosClient) -> None:
    specs = tuple(
        CosmosContainerSpec(
            name=requirement.container_name,
            partition_key_path=requirement.partition_key,
            default_ttl_seconds=requirement.ttl_seconds,
        )
        for requirement in (*USERS_COSMOS_REQUIREMENTS, *USER_ACTIVITY_COSMOS_REQUIREMENTS)
    )
    provisioner = CosmosProvisioner(client=client)
    provisioner.ensure_database()
    provisioner.ensure_containers(specs)
    provisioner.validate_containers(specs)
    assert client.health_check() is True


def _exercise_users(client: CosmosClient, *, suffix: str) -> UserDocument:
    gateway = CosmosUsersGatewayAdapter(client=client)
    user = UserDocument(
        user_id=f'user-{suffix}',
        issuer='entra',
        subject_id=f'subject-{suffix}',
        display_name=f'Integration User {suffix}',
        email=f'user-{suffix}@example.com',
        profile_key='guest',
        enabled=True,
        pending=True,
        origin='identity',
    )
    created = gateway.create_user_if_absent(user)
    assert created == user
    assert gateway.read_user(user.user_id) == user
    assert gateway.create_user_if_absent(user) == user

    identity_key = identity_lookup_key(issuer=user.issuer, subject_id=user.subject_id)
    email_key = email_lookup_key(user.email)
    identity_lookup = UserLookupDocument(
        kind='identity',
        lookup_key=identity_key,
        user_id=user.user_id,
    )
    email_lookup = UserLookupDocument(
        kind='email',
        lookup_key=email_key,
        user_id=user.user_id,
    )
    assert gateway.create_lookup_if_absent(identity_lookup) == identity_lookup
    assert gateway.create_lookup_if_absent(email_lookup) == email_lookup
    assert gateway.read_identity_lookup(identity_key) == identity_lookup
    assert gateway.read_email_lookup(email_key) == email_lookup

    discovered = CosmosDiscoveredUsersSource(client=client).list_discovered()
    assert any(item.user_id == user.user_id for item in discovered)

    persisted = client.query_items(
        container_name='users',
        query='SELECT * FROM c WHERE c.user_id = @user_id',
        parameters=[{'name': '@user_id', 'value': user.user_id}],
        cross_partition=True,
        max_items=10,
    )
    assert len(persisted) == 3
    assert {item['type'] for item in persisted} == {'user', 'user_lookup'}
    return user


def _exercise_activity(
    client: CosmosClient,
    *,
    user: UserDocument,
    suffix: str,
) -> UserActivityDocument:
    repository = CosmosUserActivityRepository(
        client=client,
        patch_operation_factory=CosmosPatchOperation,
    )
    effective_user = EffectiveUser(
        user_id=user.user_id,
        subject_id=user.subject_id or '',
        display_name=user.display_name,
        email=user.email,
        enabled=user.enabled,
        pending=user.pending,
        avatar_text='IU',
        profile=ProfileDefinition(
            key='guest',
            label='Guest',
            background_color='#6B7280',
        ),
    )
    route = ActivityRouteIdentity(
        route_key='integration-home',
        pathname='/',
        is_application_home=True,
    )
    started_at = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)
    document = UserActivityDocument.create(
        application_key='ada-integration',
        user=effective_user,
        event=_activity_event(
            suffix=suffix,
            sequence=1,
            event_type=UserActivityEventType.REGISTER,
        ),
        route=route,
        now=started_at,
    )
    repository.create(document)
    found = repository.find(document.id)
    assert found is not None
    persisted, etag = found
    assert persisted == document

    raw = client.read_item(
        container_name='user_activity',
        item_id=document.id,
        partition_key=document.id,
        include_metadata=True,
    )
    assert raw['type'] == COSMOS_USER_ACTIVITY_RECORD_TYPE
    assert raw['storage_schema_version'] == COSMOS_USER_ACTIVITY_STORAGE_SCHEMA_VERSION
    assert raw['payload']['schema_version'] == 3
    assert raw['_etag'] == etag

    updated = document.apply_event(
        user=effective_user,
        event=_activity_event(
            suffix=suffix,
            sequence=2,
            event_type=UserActivityEventType.HEARTBEAT,
        ),
        route=route,
        now=started_at + timedelta(seconds=10),
        max_active_delta_seconds=600,
        max_routes=64,
    )
    repository.replace(updated, etag=etag)
    refreshed = repository.find(document.id)
    assert refreshed is not None
    actual, current_etag = refreshed
    assert current_etag != etag
    assert actual.active_seconds == 10
    assert actual.last_sequence == 2

    with pytest.raises(UsersActivityConflictError):
        repository.replace(updated, etag=etag)
    return actual


def _activity_event(
    *,
    suffix: str,
    sequence: int,
    event_type: UserActivityEventType,
) -> UserActivityEvent:
    return UserActivityEvent(
        event_id=f'event-{suffix}-{sequence}',
        client_session_id=f'session-{suffix}',
        sequence=sequence,
        event_type=event_type,
        pathname='/',
        previous_pathname=None,
        visibility_state='visible',
        viewport=Viewport(1440, 900),
        screen=Screen(1920, 1080, 2.0),
    )


def _wait_until_ready() -> None:
    ready_url = os.environ['ATLANTICUS_COSMOS_READY_URL']
    deadline = time.monotonic() + _READY_TIMEOUT_SECONDS
    last_error: BaseException | None = None
    while time.monotonic() < deadline:
        try:
            with urlopen(ready_url, timeout=2.0) as response:
                if 200 <= response.status < 300:
                    return
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            last_error = error
        time.sleep(_READY_INTERVAL_SECONDS)
    raise RuntimeError('Cosmos emulator did not become ready') from last_error
