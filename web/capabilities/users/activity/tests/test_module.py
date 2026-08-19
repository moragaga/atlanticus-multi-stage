from pathlib import Path

from flask import Flask

from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.activity import (
    USER_ACTIVITY_ASSET_LAYER,
    USER_ACTIVITY_COSMOS_REQUIREMENTS,
    InMemoryUserActivityRepository,
    UserActivityEvent,
    create_user_activity_module,
)
from atlanticus.web.users.models import EffectiveUser
from atlanticus.web.users.profiles import ProfileDefinition


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


def _payload() -> dict[str, object]:
    return {
        'event_id': 'event-1',
        'client_session_id': 'session-1',
        'sequence': 1,
        'event_type': 'register',
        'pathname': '/alarms',
        'previous_pathname': '/',
        'visibility_state': 'visible',
        'viewport': {'width': 1440, 'height': 900},
        'screen': {'width': 1920, 'height': 1080, 'pixel_ratio': 2},
        'client_timestamp_utc': '2026-08-19T12:00:00Z',
    }


def test_user_activity_module_registers_asset_service_and_api() -> None:
    repository = InMemoryUserActivityRepository()
    module = create_user_activity_module(
        repository=repository,
        application_key='ada',
        user_provider=lambda _services: _user(),
    )
    services = ServiceRegistry()
    module.register_services(services)
    services.freeze()
    app = Flask(__name__)
    module.register_routes(app, services)

    response = app.test_client().post('/api/user-activity', json=_payload())

    assert response.status_code == 200
    assert response.get_json() == {'status': 'registered', 'tracked': True}
    assert len(repository.snapshot()) == 1
    assert module.asset_layers == (USER_ACTIVITY_ASSET_LAYER,)
    assert USER_ACTIVITY_ASSET_LAYER.load_order == 650


def test_user_activity_module_rejects_invalid_payload() -> None:
    module = create_user_activity_module(
        repository=InMemoryUserActivityRepository(),
        application_key='ada',
        user_provider=lambda _services: _user(),
    )
    services = ServiceRegistry()
    module.register_services(services)
    services.freeze()
    app = Flask(__name__)
    module.register_routes(app, services)

    response = app.test_client().post('/api/user-activity', json={'event_type': 'register'})

    assert response.status_code == 400
    assert response.get_json() == {'status': 'invalid_payload', 'tracked': False}


def test_activity_cosmos_requirement_is_ephemeral_current_state() -> None:
    requirement = USER_ACTIVITY_COSMOS_REQUIREMENTS[0]

    assert requirement.container_name == 'user_activity'
    assert requirement.partition_key == '/id'
    assert requirement.ttl_seconds == 86_400


def test_browser_collector_captures_navigation_visibility_and_screen() -> None:
    script = (
        Path(__file__).parents[1]
        / 'src/atlanticus/web/users/activity/resources/js/00_user_activity.js'
    ).read_text(encoding='utf-8')

    assert "sendEvent('route_changed'" in script
    assert "sendEvent('pagehide'" in script
    assert "sendEvent('hidden'" in script
    assert "sendEvent('visible'" in script
    assert "sendEvent('heartbeat'" in script
    assert "sendEvent('register'" in script
    assert "wrapHistory('pushState')" in script
    assert "wrapHistory('replaceState')" in script
    assert 'window.devicePixelRatio' in script
    assert 'client_timestamp_utc' not in script


def test_user_activity_event_ignores_legacy_client_timestamp() -> None:
    event = UserActivityEvent.from_payload(_payload())

    assert event.event_id == 'event-1'
    assert not hasattr(event, 'client_timestamp_utc')
