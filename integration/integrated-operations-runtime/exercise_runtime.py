from __future__ import annotations

import base64
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from integrated_operations.deployment.definition import build_deployment_definition, build_metadata
from atlanticus.web.compositions.runtime_infrastructure import WebRuntimeInfrastructure, resolve_cosmos_connections
from atlanticus.web.environment import EnvironmentReader
from atlanticus.web.users.activity import (
    COSMOS_USER_ACTIVITY_RECORD_TYPE,
    COSMOS_USER_ACTIVITY_STORAGE_SCHEMA_VERSION,
)
from atlanticus.web.users.activity.models import build_activity_document_id
from atlanticus.web.users.configuration import UserConfiguration

_HTTP_TIMEOUT_SECONDS = 60.0
_HTTP_INTERVAL_SECONDS = 0.5
_PROFILE_KEY = 'operator'
_TENANT_ID = '00000000-0000-0000-0000-000000000018'
_SUBJECT_ID = '00000000-0000-0000-0000-000000000043'
_EMAIL = 'atlanticus.r18c@example.com'
_DISPLAY_NAME = 'Atlanticus R18C Operator'
_CLIENT_SESSION_ID = 'r18c-runtime-smoke'


def main() -> None:
    base_url = os.environ['ATLANTICUS_SMOKE_APPLICATION_URL'].rstrip('/')
    live = _request_json(f'{base_url}/health/live')
    assert live['status'] == 'alive'
    assert live['application_id'] == 'ada-integrated-operations'
    assert live['environment'] == 'production'

    ready = _request_json(f'{base_url}/health/ready')
    assert ready['status'] == 'ready'

    home = _request_text(f'{base_url}/', headers=_identity_headers())
    assert 'app.min.css' in home
    assert 'Integrated Operations' in home

    activity = _request_json(
        f'{base_url}/api/user-activity',
        method='POST',
        headers={**_identity_headers(), 'Content-Type': 'application/json'},
        payload={
            'event_id': 'r18c-register',
            'client_session_id': _CLIENT_SESSION_ID,
            'sequence': 1,
            'event_type': 'register',
            'pathname': '/',
            'previous_pathname': None,
            'visibility_state': 'visible',
            'viewport': {'width': 1440, 'height': 900},
            'screen': {'width': 1920, 'height': 1080, 'pixel_ratio': 2},
        },
    )
    assert activity == {'status': 'registered', 'tracked': True}

    _assert_activity_persisted()
    print('Health live/ready: OK')
    print('Worker runtime warmup + HTTP: OK')
    print('App Service identity + Integrated Operations /: OK')
    print('Production asset snapshot: OK')
    print('User activity HTTP + Cosmos persistence: OK')
    print('R18C Integrated Operations runtime smoke passed.')


def _assert_activity_persisted() -> None:
    environment = EnvironmentReader()
    definition = build_deployment_definition(environment)
    connections = resolve_cosmos_connections(environment, definition.cosmos_connections)
    infrastructure = WebRuntimeInfrastructure(cosmos_connections=connections)
    infrastructure.open()
    try:
        user = _user()
        document_id = build_activity_document_id(
            application_key=build_metadata().application_id,
            user_id=user.user_id,
            client_session_id=_CLIENT_SESSION_ID,
        )
        raw = infrastructure.cosmos('application').read_item(
            container_name='user_activity',
            item_id=document_id,
            partition_key=document_id,
            include_metadata=True,
        )
        assert raw is not None
        assert raw['type'] == COSMOS_USER_ACTIVITY_RECORD_TYPE
        assert raw['storage_schema_version'] == COSMOS_USER_ACTIVITY_STORAGE_SCHEMA_VERSION
        assert raw['payload']['user_id'] == user.user_id
        assert raw['payload']['profile_key'] == _PROFILE_KEY
        assert raw['payload']['initial_route_key'] == 'home'
        assert raw['payload']['current_route_key'] == 'home'
        assert raw['_etag']
    finally:
        infrastructure.close()


def _user() -> UserConfiguration:
    return UserConfiguration.create(
        display_name=_DISPLAY_NAME,
        email=_EMAIL,
        profile_key=_PROFILE_KEY,
        issuer=f'app_service:aad:tenant:{_TENANT_ID}',
        subject_id=_SUBJECT_ID,
    )


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
