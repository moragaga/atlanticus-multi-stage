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


def _user(*, is_local: bool = False) -> EffectiveUser:
    profile = ProfileDefinition(key='operator', label='Operador', color='#123456')
    return EffectiveUser(
        user_id='user:1',
        subject_id='entra:1',
        display_name='User One',
        email='one@example.com',
        enabled=True,
        pending=False,
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


def test_activity_keeps_profile_resolution_that_started_the_session() -> None:
    repository = Repository()
    service = UserActivityService(
        repository=repository,
        application_key='ada',
        route_resolver=RouteResolver(),
    )
    started = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)
    initial = _user()
    changed = EffectiveUser(
        user_id=initial.user_id,
        subject_id=initial.subject_id,
        display_name=initial.display_name,
        email=initial.email,
        enabled=True,
        pending=False,
        avatar_text=initial.avatar_text,
        profile=ProfileDefinition(
            key='supervisor',
            label='Supervisor',
            color='#654321',
        ),
    )

    service.track(
        user=initial,
        event=_event(1, UserActivityEventType.REGISTER, '/'),
        now=started,
    )
    service.track(
        user=changed,
        event=_event(2, UserActivityEventType.HEARTBEAT, '/'),
        now=started + timedelta(seconds=10),
    )

    assert repository.value.profile_key == 'operator'
