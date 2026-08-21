from __future__ import annotations

import base64
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ada_application_base.definition import build_deployment_definition
from atlanticus.web.compositions.runtime_infrastructure import (
    WebRuntimeInfrastructure,
    resolve_cosmos_connections,
)
from atlanticus.web.environment import EnvironmentReader

_HTTP_TIMEOUT_SECONDS = 60.0
_HTTP_INTERVAL_SECONDS = 0.5
_TENANT_ID = '00000000-0000-0000-0000-000000000018'
_SUBJECT_ID = '00000000-0000-0000-0000-000000000044'
_EMAIL = 'atlanticus.r18d4@example.com'
_DISPLAY_NAME = 'Atlanticus R18D4 User'


def main() -> None:
    scenario = os.environ['ATLANTICUS_SMOKE_SCENARIO']
    base_url = os.environ['ATLANTICUS_SMOKE_APPLICATION_URL'].rstrip('/')
    headers = _identity_headers() if scenario != 'local-empty' else {'Accept': 'text/html'}

    live = _request_json(f'{base_url}/health/live')
    assert live['status'] == 'alive'
    assert live['application_id'] == 'ada-application-base'
    assert live['environment'] == ('local' if scenario == 'local-empty' else 'production')

    ready = _request_json(f'{base_url}/health/ready')
    assert ready['status'] == 'ready'

    home = _request_text(f'{base_url}/', headers=headers)
    assert 'id="atlanticus-runtime-config"' in home

    activity = _request_json(
        f'{base_url}/api/user-activity',
        method='POST',
        headers={**headers, 'Content-Type': 'application/json'},
        payload={
            'event_id': f'r18d4-{scenario}',
            'client_session_id': f'r18d4-{scenario}',
            'sequence': 1,
            'event_type': 'register',
            'pathname': '/',
            'previous_pathname': None,
            'visibility_state': 'visible',
            'viewport': {'width': 1440, 'height': 900},
            'screen': {'width': 1920, 'height': 1080, 'pixel_ratio': 2},
        },
    )
    if scenario == 'local-empty':
        assert activity == {'status': 'local_identity', 'tracked': False}
    else:
        assert activity == {'status': 'registered', 'tracked': True}

    _assert_cosmos_state(scenario)
    print(f'R18D.4 access smoke passed: {scenario}')


def _assert_cosmos_state(scenario: str) -> None:
    environment = EnvironmentReader()
    definition = build_deployment_definition(environment)
    connections = resolve_cosmos_connections(environment, definition.cosmos_connections)
    infrastructure = WebRuntimeInfrastructure(cosmos_connections=connections)
    infrastructure.open()
    try:
        client = infrastructure.cosmos('application')
        activities = client.query_items(
            container_name='user_activity',
            query='SELECT * FROM c',
            cross_partition=True,
        )
        users = client.query_items(
            container_name='users',
            query="SELECT * FROM c WHERE c.type = 'user'",
            cross_partition=True,
        )
        support = client.query_items(
            container_name='users_support',
            query='SELECT * FROM c',
            cross_partition=True,
        )

        if scenario == 'local-empty':
            assert activities == ()
            assert users == ()
            assert support == ()
            return

        assert len(activities) == 1
        activity = activities[0]['payload']
        assert len(users) == 1
        persisted = users[0]
        assert persisted['profile_key'] == 'guest'
        assert persisted['pending'] is True
        assert persisted['origin'] == 'identity'
        assert support == ()

        if scenario == 'production-guest':
            assert activity['profile_key'] == 'guest'
            return
        if scenario == 'production-bootstrap-admin':
            assert activity['profile_key'] == 'administrator'
            assert all(user['profile_key'] != 'administrator' for user in users)
            return
        raise RuntimeError(f'Unsupported access smoke scenario: {scenario}')
    finally:
        infrastructure.close()


def _identity_headers() -> dict[str, str]:
    principal = {
        'auth_typ': 'aad',
        'claims': [
            {'typ': 'tid', 'val': _TENANT_ID},
            {'typ': 'oid', 'val': _SUBJECT_ID},
            {'typ': 'email', 'val': _EMAIL},
            {'typ': 'name', 'val': _DISPLAY_NAME},
        ],
    }
    encoded = base64.urlsafe_b64encode(
        json.dumps(principal, separators=(',', ':')).encode('utf-8')
    ).decode('ascii')
    return {
        'Accept': 'text/html',
        'X-MS-CLIENT-PRINCIPAL': encoded,
        'X-MS-CLIENT-PRINCIPAL-ID': _SUBJECT_ID,
        'X-MS-CLIENT-PRINCIPAL-IDP': 'aad',
        'X-MS-CLIENT-PRINCIPAL-NAME': _EMAIL,
    }


def _request_text(
    url: str,
    *,
    method: str = 'GET',
    headers: dict[str, str] | None = None,
    payload: dict[str, object] | None = None,
) -> str:
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    deadline = time.monotonic() + _HTTP_TIMEOUT_SECONDS
    last_error: BaseException | None = None
    while time.monotonic() < deadline:
        try:
            request = Request(url, data=data, method=method, headers=headers or {})
            with urlopen(request, timeout=3.0) as response:
                return response.read().decode('utf-8')
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            last_error = error
        time.sleep(_HTTP_INTERVAL_SECONDS)
    raise RuntimeError(f'HTTP request did not succeed: {url}') from last_error


def _request_json(
    url: str,
    *,
    method: str = 'GET',
    headers: dict[str, str] | None = None,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    return json.loads(_request_text(url, method=method, headers=headers, payload=payload))


if __name__ == '__main__':
    main()
