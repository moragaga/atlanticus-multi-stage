from __future__ import annotations

import base64
import json
import os
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from dash import html
from flask import Flask

from ada.compositions.web_bootstrap import (
    AdaConfigurationBackends,
    AdaCosmosBindings,
    create_ada_web_bootstrap,
    ensure_ada_cosmos_infrastructure,
    synchronize_ada_access_projections,
)
from ada.configuration.tools import TOOL_COSMOS_REQUIREMENTS
from ada.configuration.tools.adapters import (
    CosmosToolProjectionRepository,
    CosmosToolProjectionSettings,
    SharePointToolConfigurationSettings,
    SharePointToolConfigurationStore,
)
from atlanticus.configuration import ConfigurationBootstrap
from atlanticus.connectivity.cosmos import CosmosSettings
from atlanticus.kernel import Environment
from atlanticus.web.application import create_web_application
from atlanticus.web.compositions.runtime_infrastructure import (
    WebRuntimeInfrastructure,
    create_sharepoint_configuration_specs,
    resolve_sharepoint_infrastructure_settings,
)
from atlanticus.web.identity.app_service import create_app_service_identity_provider
from atlanticus.web.models import ApplicationMetadata, WebApplicationDefinition
from atlanticus.web.modules import WebModule
from atlanticus.web.navigation.api import resolve_navigation_from_services
from atlanticus.web.navigation.configuration import (
    NAVIGATION_COSMOS_REQUIREMENTS,
    NavigationConfigurationBundle,
    NavigationConfigurationCatalog,
    NavigationConfigurationSourceDocument,
    NavigationLinkConfiguration,
    encode_navigation_configuration_source,
)
from atlanticus.web.navigation.configuration.adapters import (
    CosmosNavigationProjectionRepository,
    CosmosNavigationProjectionSettings,
    SharePointNavigationConfigurationSettings,
    SharePointNavigationConfigurationStore,
)
from atlanticus.web.users.activity import (
    COSMOS_USER_ACTIVITY_RECORD_TYPE,
    COSMOS_USER_ACTIVITY_STORAGE_SCHEMA_VERSION,
)
from atlanticus.web.users.activity.models import build_activity_document_id
from atlanticus.web.users.configuration import (
    UsersConfigurationBundle,
    UsersConfigurationCatalog,
    UsersConfigurationSourceDocument,
    UserConfiguration,
    UserProfileConfiguration,
    encode_users_configuration_source,
)
from atlanticus.web.users.configuration.adapters import (
    SharePointUsersConfigurationSettings,
    SharePointUsersConfigurationStore,
)
from atlanticus.web.users.cosmos import (
    CosmosDiscoveredUsersSource,
    CosmosUsersProjectionRepository,
)

_READY_TIMEOUT_SECONDS = 120.0
_READY_INTERVAL_SECONDS = 1.0
_CONNECTION_NAME = 'application'
_APPLICATION_ID = 'ada-full-application-e2e'
_PROFILE_KEY = 'operator'
_RESTRICTED_PROFILE_KEY = 'supervisor'
_TENANT_ID = '00000000-0000-0000-0000-000000000017'
_SUBJECT_ID = '00000000-0000-0000-0000-000000000042'
_EMAIL = 'atlanticus.e2e@example.com'
_DISPLAY_NAME = 'Atlanticus E2E Operator'
_USERS_FILENAME = '__atlanticus_full_e2e_users_configuration.json.gz'
_NAVIGATION_FILENAME = '__atlanticus_full_e2e_navigation_configuration.json.gz'
_TOOL_FILENAME = '__atlanticus_full_e2e_tool_configuration.json.gz'


def test_ada_full_application_end_to_end() -> None:
    _wait_until_ready()
    database_name = f'ada-full-it-{uuid.uuid4().hex[:8]}'
    cosmos_settings = CosmosSettings(
        endpoint=_required_environment('ATLANTICUS_COSMOS_ENDPOINT'),
        key=_required_environment('ATLANTICUS_COSMOS_KEY'),
        database_name=database_name,
        allow_insecure_http=True,
        max_query_items=100,
        page_size=50,
    )
    connections = {_CONNECTION_NAME: cosmos_settings}
    bindings = AdaCosmosBindings(
        users=_CONNECTION_NAME,
        activity=_CONNECTION_NAME,
        navigation=_CONNECTION_NAME,
        tools=_CONNECTION_NAME,
    )

    provisioning = ensure_ada_cosmos_infrastructure(
        cosmos_connections=connections,
        bindings=bindings,
        create_databases_if_missing=True,
    )
    assert _CONNECTION_NAME in provisioning.databases_created
    assert set(provisioning.containers_created[_CONNECTION_NAME]) == {
        'users',
        'users_support',
        'user_activity',
        'configuration',
    }

    sharepoint_settings = _resolve_sharepoint_settings()
    synchronization_infrastructure = WebRuntimeInfrastructure(
        cosmos_connections=connections,
        sharepoint=sharepoint_settings,
    )
    synchronization_infrastructure.open()
    try:
        user = _seed_sharepoint_access_configuration(synchronization_infrastructure)
        configuration = _create_e2e_configuration_backends(
            synchronization_infrastructure,
            bindings=bindings,
        )
        first_sync = synchronize_ada_access_projections(
            configuration=configuration,
            actor='ada-full-e2e',
        )
        assert first_sync.users_projected is True
        assert first_sync.navigation_projected is True
        second_sync = synchronize_ada_access_projections(
            configuration=configuration,
            actor='ada-full-e2e',
        )
        assert second_sync.users_projected is False
        assert second_sync.navigation_projected is False
    finally:
        synchronization_infrastructure.close()

    runtime_infrastructure = WebRuntimeInfrastructure(cosmos_connections=connections)
    runtime_infrastructure.open()
    try:
        metadata = ApplicationMetadata(
            application_id=_APPLICATION_ID,
            display_name='ADA Full E2E',
            version='0.1.0',
        )
        bootstrap = create_ada_web_bootstrap(
            metadata=metadata,
            identity_provider=create_app_service_identity_provider(),
            infrastructure=runtime_infrastructure,
            bindings=bindings,
        )
        assert bootstrap.infrastructure is runtime_infrastructure
        runtime = create_web_application(
            WebApplicationDefinition(
                import_name='ada.compositions.web_bootstrap',
                metadata=metadata,
                publications_root=Path('/tmp/atlanticus-ada-full-e2e-assets'),
                layout=_layout,
                modules=(*bootstrap.modules, _create_e2e_module()),
                page_packages=('e2e_pages',),
            )
        )
        _exercise_application(runtime.server, user_id=user.user_id)
        _assert_activity_persisted(
            runtime_infrastructure,
            user_id=user.user_id,
            client_session_id='full-e2e-session',
        )
        _assert_projections_persisted(runtime_infrastructure)
        print(f'Cosmos database: {database_name}')
        print(f'Cosmos connection: {_CONNECTION_NAME}')
        print(f'Users path: {sharepoint_settings.paths.users_relative_path}/{_USERS_FILENAME}')
        print(
            'Navigation path: '
            f'{sharepoint_settings.paths.navigation_relative_path}/{_NAVIGATION_FILENAME}'
        )
        print(f'Activity user: {user.user_id}')
    finally:
        runtime_infrastructure.close()


def _resolve_sharepoint_settings():
    specs = create_sharepoint_configuration_specs()
    bootstrap = ConfigurationBootstrap.from_process(
        specs=specs,
        process_values=os.environ,
    )
    configuration = bootstrap.load(process_values=os.environ)
    assert configuration.environment == Environment.from_value('local')
    return resolve_sharepoint_infrastructure_settings(configuration)


def _seed_sharepoint_access_configuration(
    infrastructure: WebRuntimeInfrastructure,
) -> UserConfiguration:
    gateway = infrastructure.sharepoint()
    paths = infrastructure.sharepoint_paths
    user = UserConfiguration.create(
        display_name=_DISPLAY_NAME,
        email=_EMAIL,
        profile_key=_PROFILE_KEY,
        issuer=f'app_service:aad:tenant:{_TENANT_ID}',
        subject_id=_SUBJECT_ID,
    )
    users_bundle = UsersConfigurationBundle.create(
        catalog=UsersConfigurationCatalog(
            profiles=(
                UserProfileConfiguration(
                    key=_PROFILE_KEY,
                    label='Operator',
                    background_color='#455A64',
                ),
                UserProfileConfiguration(
                    key=_RESTRICTED_PROFILE_KEY,
                    label='Supervisor',
                    background_color='#546E7A',
                ),
            ),
            users=(user,),
        ),
        saved_by='ada-full-e2e',
    )
    navigation_bundle = NavigationConfigurationBundle.create(
        catalog=NavigationConfigurationCatalog(
            links=(
                NavigationLinkConfiguration(
                    key='home',
                    label='Inicio',
                    href='/',
                    allowed_profiles=(_PROFILE_KEY,),
                ),
                NavigationLinkConfiguration(
                    key='allowed',
                    label='Permitido',
                    href='/allowed',
                    allowed_profiles=(_PROFILE_KEY,),
                ),
                NavigationLinkConfiguration(
                    key='restricted',
                    label='Restringido',
                    href='/restricted',
                    allowed_profiles=(_RESTRICTED_PROFILE_KEY,),
                ),
            )
        ),
        saved_by='ada-full-e2e',
    )
    gateway.write(
        filename=_USERS_FILENAME,
        relative_path=paths.users_relative_path,
        content=_encode(
            encode_users_configuration_source(
                UsersConfigurationSourceDocument.from_bundle(users_bundle)
            )
        ),
    )
    gateway.write(
        filename=_NAVIGATION_FILENAME,
        relative_path=paths.navigation_relative_path,
        content=_encode(
            encode_navigation_configuration_source(
                NavigationConfigurationSourceDocument.from_bundle(navigation_bundle)
            )
        ),
    )
    return user


def _create_e2e_configuration_backends(
    infrastructure: WebRuntimeInfrastructure,
    *,
    bindings: AdaCosmosBindings,
) -> AdaConfigurationBackends:
    users_client = infrastructure.cosmos(bindings.users)
    navigation_client = infrastructure.cosmos(bindings.navigation)
    tools_client = infrastructure.cosmos(bindings.tools)
    gateway = infrastructure.sharepoint()
    paths = infrastructure.sharepoint_paths
    return AdaConfigurationBackends(
        users_source=SharePointUsersConfigurationStore(
            gateway=gateway,
            settings=SharePointUsersConfigurationSettings(
                filename=_USERS_FILENAME,
                relative_path=paths.users_relative_path,
            ),
        ),
        users_projection=CosmosUsersProjectionRepository(client=users_client),
        users_discovered=CosmosDiscoveredUsersSource(client=users_client),
        navigation_source=SharePointNavigationConfigurationStore(
            gateway=gateway,
            settings=SharePointNavigationConfigurationSettings(
                filename=_NAVIGATION_FILENAME,
                relative_path=paths.navigation_relative_path,
            ),
        ),
        navigation_projection=CosmosNavigationProjectionRepository(
            client=navigation_client,
            settings=CosmosNavigationProjectionSettings(
                container_name=NAVIGATION_COSMOS_REQUIREMENTS[0].container_name,
            ),
        ),
        tools_source=SharePointToolConfigurationStore(
            gateway=gateway,
            settings=SharePointToolConfigurationSettings(
                filename=_TOOL_FILENAME,
                relative_path=paths.tool_relative_path,
            ),
        ),
        tools_projection=CosmosToolProjectionRepository(
            client=tools_client,
            settings=CosmosToolProjectionSettings(
                container_name=TOOL_COSMOS_REQUIREMENTS[0].container_name,
            ),
        ),
    )


def _create_e2e_module() -> WebModule:
    def register_routes(server: Flask, services) -> None:
        @server.get('/allowed')
        def allowed() -> tuple[str, int]:
            return 'allowed', 200

        @server.get('/restricted')
        def restricted() -> tuple[str, int]:
            return 'restricted', 200

        @server.get('/api/e2e/navigation')
        def navigation_state() -> tuple[dict[str, object], int]:
            menu = resolve_navigation_from_services(services)
            return {
                'display_name': menu.user.display_name,
                'profile_key': menu.user.profile_key,
                'links': [link.key for link in menu.links],
            }, 200

    return WebModule(name='ada-full-e2e', register_routes=register_routes)


def _layout(_services):
    return html.Div('ADA Full E2E')


def _exercise_application(server: Flask, *, user_id: str) -> None:
    client = server.test_client()
    headers = _identity_headers()
    home = client.get('/', headers=headers)
    assert home.status_code == 200

    allowed = client.get('/allowed', headers=headers)
    assert allowed.status_code == 200
    assert allowed.get_data(as_text=True) == 'allowed'

    navigation = client.get('/api/e2e/navigation', headers=headers)
    assert navigation.status_code == 200
    assert navigation.get_json() == {
        'display_name': _DISPLAY_NAME,
        'profile_key': _PROFILE_KEY,
        'links': ['home', 'allowed'],
    }

    restricted = client.get('/restricted', headers=headers)
    assert restricted.status_code == 403

    activity = client.post(
        '/api/user-activity',
        headers={**headers, 'Content-Type': 'application/json'},
        json={
            'event_id': 'full-e2e-register',
            'client_session_id': 'full-e2e-session',
            'sequence': 1,
            'event_type': 'register',
            'pathname': '/allowed',
            'previous_pathname': None,
            'visibility_state': 'visible',
            'viewport': {'width': 1440, 'height': 900},
            'screen': {'width': 1920, 'height': 1080, 'pixel_ratio': 2},
        },
    )
    assert activity.status_code == 200
    assert activity.get_json() == {'status': 'registered', 'tracked': True}


def _assert_activity_persisted(
    infrastructure: WebRuntimeInfrastructure,
    *,
    user_id: str,
    client_session_id: str,
) -> None:
    document_id = build_activity_document_id(
        application_key=_APPLICATION_ID,
        user_id=user_id,
        client_session_id=client_session_id,
    )
    raw = infrastructure.cosmos(_CONNECTION_NAME).read_item(
        container_name='user_activity',
        item_id=document_id,
        partition_key=document_id,
        include_metadata=True,
    )
    assert raw is not None
    assert raw['type'] == COSMOS_USER_ACTIVITY_RECORD_TYPE
    assert raw['storage_schema_version'] == COSMOS_USER_ACTIVITY_STORAGE_SCHEMA_VERSION
    assert raw['payload']['user_id'] == user_id
    assert raw['payload']['profile_key'] == _PROFILE_KEY
    assert raw['payload']['initial_route_key'] == 'allowed'
    assert raw['payload']['current_route_key'] == 'allowed'
    assert raw['payload']['schema_version'] == 3
    assert raw['_etag']


def _assert_projections_persisted(infrastructure: WebRuntimeInfrastructure) -> None:
    client = infrastructure.cosmos(_CONNECTION_NAME)
    users_state = client.read_item(
        container_name='users_support',
        item_id='users',
        partition_key='system',
    )
    assert users_state is not None
    assert users_state['projection_status'] == 'ready'
    assert users_state['source_revision']

    navigation = client.read_item(
        container_name='configuration',
        item_id='navigation',
        partition_key='navigation',
    )
    assert navigation is not None
    assert navigation['source_revision']


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


def _encode(value: bytes) -> str:
    return base64.b64encode(value).decode('ascii')


def _required_environment(name: str) -> str:
    value = os.getenv(name, '').strip()
    if not value:
        raise RuntimeError(f'{name} is required')
    return value


def _wait_until_ready() -> None:
    ready_url = _required_environment('ATLANTICUS_COSMOS_READY_URL')
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
