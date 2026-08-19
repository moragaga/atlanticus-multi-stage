from datetime import UTC, datetime

import pytest

from atlanticus.web.users.activity import (
    ActivityRouteIdentity,
    CosmosUserActivityRepository,
    InMemoryUserActivityRepository,
    Screen,
    UserActivityDocument,
    UserActivityEvent,
    UserActivityEventType,
    Viewport,
)
from atlanticus.web.users.activity.errors import UsersActivityConflictError
from atlanticus.web.users.models import EffectiveUser
from atlanticus.web.users.profiles import ProfileDefinition


class CosmosConflictError(Exception):
    pass


class CosmosClient:
    def __init__(self) -> None:
        self.document = None
        self.etag = '1'
        self.fail_create = False
        self.fail_replace = False

    def find_item(
        self,
        *,
        container_name,
        item_id,
        partition_key,
        include_metadata=False,
    ):
        assert container_name == 'user_activity'
        assert partition_key == item_id
        if self.document is None:
            return None
        result = dict(self.document)
        if include_metadata:
            result['_etag'] = self.etag
        return result

    def create_item(self, *, container_name, item, include_metadata=False):
        assert container_name == 'user_activity'
        if self.fail_create:
            raise CosmosConflictError()
        self.document = dict(item)
        return dict(item)

    def replace_item(
        self,
        *,
        container_name,
        item_id,
        partition_key,
        item,
        if_match_etag=None,
        include_metadata=False,
    ):
        assert container_name == 'user_activity'
        assert item_id == partition_key == item['id']
        assert if_match_etag == self.etag
        if self.fail_replace:
            raise CosmosConflictError()
        self.document = dict(item)
        self.etag = str(int(self.etag) + 1)
        return dict(item)


def _user() -> EffectiveUser:
    return EffectiveUser(
        user_id='user:1',
        subject_id='entra:1',
        display_name='User One',
        email='one@example.com',
        enabled=True,
        pending=False,
        avatar_text='UO',
        profile=ProfileDefinition(
            key='operator',
            label='Operador',
            background_color='#123456',
        ),
    )


def _document() -> UserActivityDocument:
    return UserActivityDocument.create(
        application_key='ada',
        user=_user(),
        event=UserActivityEvent(
            event_id='event-1',
            client_session_id='session-1',
            sequence=1,
            event_type=UserActivityEventType.REGISTER,
            pathname='/alarms',
            previous_pathname='/',
            visibility_state='visible',
            viewport=Viewport(1440, 900),
            screen=Screen(1920, 1080, 2.0),
        ),
        route=ActivityRouteIdentity(route_key='alarms', pathname='/alarms'),
        now=datetime(2026, 8, 19, 12, 0, tzinfo=UTC),
    )


def test_activity_document_round_trips_persisted_schema() -> None:
    document = _document()

    restored = UserActivityDocument.from_document(document.to_document())

    assert restored == document
    assert restored.profile_key == 'operator'
    assert restored.initial_route_key == 'alarms'
    assert restored.initial_pathname == '/alarms'
    assert restored.current_route_key == 'alarms'
    assert restored.last_screen.pixel_ratio == 2.0


def test_memory_repository_uses_optimistic_concurrency() -> None:
    repository = InMemoryUserActivityRepository()
    document = _document()

    repository.create(document)
    found, etag = repository.find(document.id)

    assert found == document
    repository.replace(document, etag=etag)
    with pytest.raises(UsersActivityConflictError):
        repository.replace(document, etag=etag)


def test_cosmos_repository_uses_id_partition_and_etag() -> None:
    client = CosmosClient()
    repository = CosmosUserActivityRepository(client=client)
    document = _document()

    repository.create(document)
    found = repository.find(document.id)

    assert found is not None
    restored, etag = found
    assert restored == document
    assert etag == '1'
    repository.replace(restored, etag=etag)
    assert client.etag == '2'


def test_cosmos_repository_maps_concurrency_errors() -> None:
    client = CosmosClient()
    client.fail_create = True
    repository = CosmosUserActivityRepository(client=client)

    with pytest.raises(UsersActivityConflictError):
        repository.create(_document())
