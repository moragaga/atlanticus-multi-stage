from datetime import UTC, datetime, timedelta

from atlanticus.web.users.activity import (
    ActivityRouteIdentity,
    Screen,
    UserActivityEvent,
    UserActivityEventType,
    UserActivityService,
    Viewport,
)
from atlanticus.web.users.activity.errors import UsersActivityConflictError
from atlanticus.web.users.models import EffectiveUser
from atlanticus.web.users.profiles import ProfileDefinition


class RouteResolver:
    def resolve(self, pathname: str) -> ActivityRouteIdentity:
        if pathname == '/':
            return ActivityRouteIdentity(
                route_key='dashboard',
                pathname='/',
                is_application_home=True,
            )
        return ActivityRouteIdentity(route_key='process', pathname=pathname)


class Repository:
    def __init__(self) -> None:
        self.value = None
        self.etag = '1'

    def find(self, _document_id):
        return None if self.value is None else (self.value, self.etag)

    def create(self, document):
        if self.value is not None:
            raise UsersActivityConflictError()
        self.value = document

    def replace(self, document, *, etag):
        assert etag == self.etag
        self.value = document
        self.etag = str(int(self.etag) + 1)


def _user(*, profile_key: str = 'operator', is_local: bool = False) -> EffectiveUser:
    profile = ProfileDefinition(
        key=profile_key,
        label=profile_key.title(),
        background_color='#123456',
    )
    return EffectiveUser(
        user_id='user:1',
        subject_id='entra:1',
        display_name='User One',
        email='one@example.com',
        enabled=True,
        pending=profile_key == 'guest',
        avatar_text='UO',
        profile=profile,
        is_local=is_local,
    )


def _event(sequence: int, event_type: UserActivityEventType, pathname: str):
    return UserActivityEvent(
        event_id=f'event-{sequence}',
        client_session_id='session-1',
        sequence=sequence,
        event_type=event_type,
        pathname=pathname,
        previous_pathname=None,
        visibility_state='visible',
        viewport=Viewport(1440, 900),
        screen=Screen(1920, 1080, 1.0),
    )


def test_activity_preserves_profile_resolution_and_home_route_identity() -> None:
    repository = Repository()
    service = UserActivityService(
        repository=repository,
        application_key='ada',
        route_resolver=RouteResolver(),
    )
    started = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)

    service.track(
        user=_user(),
        event=_event(1, UserActivityEventType.REGISTER, '/'),
        now=started,
    )
    service.track(
        user=_user(),
        event=_event(2, UserActivityEventType.ROUTE_CHANGED, '/process/flotacion'),
        now=started + timedelta(seconds=30),
    )

    document = repository.value
    assert document.profile_key == 'operator'
    assert document.initial_route_key == 'dashboard'
    assert document.initial_pathname == '/'
    assert document.initial_viewport.width == 1440
    assert document.initial_screen.width == 1920
    assert document.routes['dashboard'].is_application_home is True
    assert document.routes['dashboard'].pathname == '/'
    assert document.routes['process'].pathname == '/process/flotacion'


def test_local_users_are_not_tracked() -> None:
    repository = Repository()
    service = UserActivityService(
        repository=repository,
        application_key='ada',
        route_resolver=RouteResolver(),
    )

    result = service.track(
        user=_user(is_local=True),
        event=_event(1, UserActivityEventType.REGISTER, '/'),
    )

    assert result == {'status': 'local_identity', 'tracked': False}
    assert repository.value is None


def test_activity_refreshes_profile_without_resetting_session_state() -> None:
    repository = Repository()
    service = UserActivityService(
        repository=repository,
        application_key='ada',
        route_resolver=RouteResolver(),
    )
    started = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)
    initial = _user(profile_key='guest')
    changed = _user(profile_key='supervisor')

    service.track(
        user=initial,
        event=_event(1, UserActivityEventType.REGISTER, '/'),
        now=started,
    )
    initial_document = repository.value

    service.track(
        user=changed,
        event=_event(2, UserActivityEventType.HEARTBEAT, '/'),
        now=started + timedelta(seconds=10),
    )

    document = repository.value
    assert document.id == initial_document.id
    assert document.client_session_id == initial_document.client_session_id
    assert document.profile_key == 'supervisor'
    assert document.first_seen_at_utc == initial_document.first_seen_at_utc
    assert document.initial_route_key == initial_document.initial_route_key
    assert document.initial_pathname == initial_document.initial_pathname
    assert document.page_views == initial_document.page_views
    assert document.active_seconds == 10
