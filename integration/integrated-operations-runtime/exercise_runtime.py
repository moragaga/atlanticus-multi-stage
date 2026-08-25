from __future__ import annotations

import base64
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ada.configuration.tools import TOOL_COSMOS_REQUIREMENTS
from atlanticus.web.compositions.runtime_infrastructure import (
    WebRuntimeInfrastructure,
    resolve_cosmos_connections,
)
from atlanticus.web.environment import EnvironmentReader
from atlanticus.web.users.activity import (
    COSMOS_USER_ACTIVITY_RECORD_TYPE,
    COSMOS_USER_ACTIVITY_STORAGE_SCHEMA_VERSION,
)
from atlanticus.web.users.activity.models import build_activity_document_id
from atlanticus.web.users.configuration import UserConfiguration
from integrated_operations.deployment.definition import (
    build_deployment_definition,
    build_metadata,
)

_HTTP_TIMEOUT_SECONDS = 60.0
_HTTP_INTERVAL_SECONDS = 0.5
_PROFILE_KEY = 'operator'
_TENANT_ID = '00000000-0000-0000-0000-000000000018'
_SUBJECT_ID = '00000000-0000-0000-0000-000000000043'
_EMAIL = 'atlanticus.r18c@example.com'
_DISPLAY_NAME = 'Atlanticus R18C Operator'
_ADMIN_SUBJECT_ID = '00000000-0000-0000-0000-000000000044'
_ADMIN_EMAIL = 'atlanticus.r18c.admin@example.com'
_ADMIN_DISPLAY_NAME = 'Atlanticus R18C Administrator'
_CLIENT_SESSION_ID = 'r19b2-runtime-smoke'
_PROJECTED_MILL_DISPLAY_NAME = 'Molienda proyectada R19B2'
_KPI_ACTIVE_KEY = 'produccion_total'
_KPI_DISABLED_KEY = 'kpi_temporalmente_deshabilitado'
_KPI_SNAPSHOT_PATH_VARIABLE = 'ATLANTICUS_KPI_PROJECTION_SNAPSHOT_PATH'


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

    dash_layout = _request_json(
        f'{base_url}/_dash-layout',
        headers=_identity_headers(),
    )
    dash_layout_json = json.dumps(dash_layout, ensure_ascii=False)
    assert _PROJECTED_MILL_DISPLAY_NAME in dash_layout_json
    assert 'data-ada-unified-application' in dash_layout_json
    assert 'app-header-offcanvas' in dash_layout_json
    assert 'app-header-desktop-toggle' in dash_layout_json
    assert '"data-ada-surface-adapter": "integrated_operations"' in dash_layout_json

    manager_surface = _request_json(
        f'{base_url}/_dash-update-component',
        method='POST',
        headers={**_admin_identity_headers(), 'Content-Type': 'application/json'},
        payload={
            'output': 'ada-unified-application-surface-host.children',
            'outputs': {
                'id': 'ada-unified-application-surface-host',
                'property': 'children',
            },
            'inputs': [
                {
                    'id': 'ada-unified-application-location',
                    'property': 'pathname',
                    'value': '/manager/tools',
                }
            ],
            'state': [],
            'changedPropIds': ['ada-unified-application-location.pathname'],
        },
    )
    manager_surface_json = json.dumps(manager_surface, ensure_ascii=False)
    assert 'data-ada-manager-surface' in manager_surface_json
    assert 'atlanticus-manager-refresh' in manager_surface_json
    assert 'app-header-desktop-toggle' in manager_surface_json
    assert 'atlanticus-manager-content' in manager_surface_json

    manager_content = _request_json(
        f'{base_url}/_dash-update-component',
        method='POST',
        headers={**_admin_identity_headers(), 'Content-Type': 'application/json'},
        payload={
            'output': 'atlanticus-manager-content.children',
            'outputs': {
                'id': 'atlanticus-manager-content',
                'property': 'children',
            },
            'inputs': [
                {
                    'id': 'atlanticus-manager-location',
                    'property': 'pathname',
                    'value': '/manager/tools',
                }
            ],
            'state': [],
            'changedPropIds': ['atlanticus-manager-location.pathname'],
        },
    )
    manager_content_json = json.dumps(manager_content, ensure_ascii=False)
    assert 'ada-tools-configuration-store' in manager_content_json
    assert 'Configuración única de herramienta' in manager_content_json
    assert 'ada-tools-selected-tool' not in manager_content_json

    kpi_manager_content = _request_json(
        f'{base_url}/_dash-update-component',
        method='POST',
        headers={**_admin_identity_headers(), 'Content-Type': 'application/json'},
        payload={
            'output': 'atlanticus-manager-content.children',
            'outputs': {
                'id': 'atlanticus-manager-content',
                'property': 'children',
            },
            'inputs': [
                {
                    'id': 'atlanticus-manager-location',
                    'property': 'pathname',
                    'value': '/manager/kpis',
                }
            ],
            'state': [],
            'changedPropIds': ['atlanticus-manager-location.pathname'],
        },
    )
    kpi_manager_content_json = json.dumps(kpi_manager_content, ensure_ascii=False)
    assert 'ada-kpis-configuration-store' in kpi_manager_content_json
    assert 'Primero configura y proyecta una herramienta ADA' in kpi_manager_content_json
    assert 'Ir a Herramientas' in kpi_manager_content_json
    assert 'ada-kpis-selected-tool' not in kpi_manager_content_json
    assert 'slot_keys' not in kpi_manager_content_json

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
    kpi_projection = _assert_kpi_projection_persisted()
    _write_kpi_projection_snapshot(kpi_projection)
    print('Health live/ready: OK')
    print('Worker runtime warmup + HTTP: OK')
    print('App Service identity + projected Integrated Operations /: OK')
    print('Unified presentation shell + generic ADA surface adapter: OK')
    print('Unified Manager surface composition + deep route: OK')
    print('Unified runtime + authorization convergence: OK')
    print('Single Tool Configuration + singular projection: OK')
    print('KPI Manager route + Tool Projection dependency: OK')
    print('KPI Source SharePoint + KPI Projection Cosmos: OK')
    print('KPI Cosmos projection snapshot: OK')
    print('Production asset snapshot: OK')
    print('User activity HTTP + Cosmos persistence: OK')
    print('R19B.2 Projected Tool Runtime smoke passed.')


def _assert_kpi_projection_persisted() -> dict[str, object]:
    environment = EnvironmentReader()
    definition = build_deployment_definition(environment)
    connections = resolve_cosmos_connections(environment, definition.cosmos_connections)
    infrastructure = WebRuntimeInfrastructure(cosmos_connections=connections)
    infrastructure.open()
    try:
        if len(TOOL_COSMOS_REQUIREMENTS) != 1:
            raise AssertionError('Expected one Tools configuration container')
        container_name = TOOL_COSMOS_REQUIREMENTS[0].container_name
        raw = infrastructure.cosmos('application').read_item(
            container_name=container_name,
            item_id='kpis',
            partition_key='kpis',
            include_metadata=True,
        )
        assert raw is not None
        assert raw['id'] == 'kpis'
        assert raw['partition_key'] == 'kpis'
        assert raw['document_type'] == 'ada_kpi_configuration_projection'
        assert raw['schema_version'] == 1
        assert str(raw['revision']).strip()
        assert str(raw['source_revision']).strip()
        assert str(raw['tool_projection_revision']).strip()
        configuration = raw['configuration']
        assert isinstance(configuration, dict)
        bindings = configuration['bindings']
        assert isinstance(bindings, list)
        by_key = {str(binding['key']): binding for binding in bindings}
        active = by_key[_KPI_ACTIVE_KEY]
        assert active['destination_keys'] == ['global_indicators', 'molienda']
        assert active['latest_enabled'] is True
        assert active['series_enabled'] is True
        assert active['series_hours'] == 24
        disabled = by_key[_KPI_DISABLED_KEY]
        assert disabled['destination_keys'] == ['time_status']
        assert disabled['latest_enabled'] is False
        assert disabled['series_enabled'] is False
        assert disabled['series_hours'] is None
        return dict(raw)
    finally:
        infrastructure.close()


def _write_kpi_projection_snapshot(document: dict[str, object]) -> None:
    path = os.environ.get(_KPI_SNAPSHOT_PATH_VARIABLE, '').strip()
    if not path:
        return
    snapshot_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
    with open(snapshot_path, 'w', encoding='utf-8') as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write('\n')


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
    return _headers_for_identity(
        subject_id=_SUBJECT_ID,
        email=_EMAIL,
        display_name=_DISPLAY_NAME,
    )


def _admin_identity_headers() -> dict[str, str]:
    return _headers_for_identity(
        subject_id=_ADMIN_SUBJECT_ID,
        email=_ADMIN_EMAIL,
        display_name=_ADMIN_DISPLAY_NAME,
    )


def _headers_for_identity(
    *,
    subject_id: str,
    email: str,
    display_name: str,
) -> dict[str, str]:
    principal = {
        'auth_typ': 'aad',
        'claims': [
            {'typ': 'tid', 'val': _TENANT_ID},
            {'typ': 'oid', 'val': subject_id},
            {'typ': 'email', 'val': email},
            {'typ': 'name', 'val': display_name},
        ],
    }
    encoded = base64.urlsafe_b64encode(
        json.dumps(principal, separators=(',', ':')).encode('utf-8')
    ).decode('ascii')
    return {
        'Accept': 'text/html',
        'X-MS-CLIENT-PRINCIPAL': encoded,
        'X-MS-CLIENT-PRINCIPAL-ID': subject_id,
        'X-MS-CLIENT-PRINCIPAL-IDP': 'aad',
        'X-MS-CLIENT-PRINCIPAL-NAME': email,
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
