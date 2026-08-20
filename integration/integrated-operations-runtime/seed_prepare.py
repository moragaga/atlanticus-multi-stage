from __future__ import annotations

import base64
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from ada.compositions.web_deployment import prepare_ada_web_deployment
from integrated_operations.deployment.definition import build_deployment_definition
from atlanticus.web.compositions.runtime_infrastructure import (
    WebRuntimeInfrastructure,
    resolve_sharepoint_infrastructure_settings,
)
from atlanticus.web.environment import EnvironmentReader
from atlanticus.web.navigation.configuration import (
    NavigationConfigurationBundle,
    NavigationConfigurationCatalog,
    NavigationConfigurationSourceDocument,
    NavigationLinkConfiguration,
    encode_navigation_configuration_source,
)
from atlanticus.web.users.configuration import (
    UsersConfigurationBundle,
    UsersConfigurationCatalog,
    UsersConfigurationSourceDocument,
    UserConfiguration,
    UserProfileConfiguration,
    encode_users_configuration_source,
)

_READY_TIMEOUT_SECONDS = 120.0
_READY_INTERVAL_SECONDS = 1.0
_PROFILE_KEY = 'operator'
_TENANT_ID = '00000000-0000-0000-0000-000000000018'
_SUBJECT_ID = '00000000-0000-0000-0000-000000000043'
_EMAIL = 'atlanticus.r18c@example.com'
_DISPLAY_NAME = 'Atlanticus R18C Operator'


def main() -> None:
    _wait_until_ready()
    environment = EnvironmentReader()
    definition = build_deployment_definition(environment)
    sharepoint_settings = resolve_sharepoint_infrastructure_settings(
        environment,
        definition.sharepoint,
    )
    infrastructure = WebRuntimeInfrastructure(cosmos_connections={}, sharepoint=sharepoint_settings)
    infrastructure.open()
    try:
        gateway = infrastructure.sharepoint()
        paths = infrastructure.sharepoint_paths
        user = _user()
        users_bundle = UsersConfigurationBundle.create(
            catalog=UsersConfigurationCatalog(
                profiles=(
                    UserProfileConfiguration(
                        key=_PROFILE_KEY,
                        label='Operator',
                        background_color='#455A64',
                    ),
                ),
                users=(user,),
            ),
            saved_by='ada-r18c-smoke',
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
                )
            ),
            saved_by='ada-r18c-smoke',
        )
        gateway.write(
            filename=definition.configuration_filenames.users,
            relative_path=paths.users_relative_path,
            content=_encode(
                encode_users_configuration_source(
                    UsersConfigurationSourceDocument.from_bundle(users_bundle)
                )
            ),
        )
        gateway.write(
            filename=definition.configuration_filenames.navigation,
            relative_path=paths.navigation_relative_path,
            content=_encode(
                encode_navigation_configuration_source(
                    NavigationConfigurationSourceDocument.from_bundle(navigation_bundle)
                )
            ),
        )
    finally:
        infrastructure.close()

    result = prepare_ada_web_deployment(
        definition=definition,
        environment=environment,
        create_databases_if_missing=True,
        actor='ada-r18c-smoke',
    )
    assert 'application' in result.provisioning.databases_created
    assert set(result.provisioning.containers_created['application']) == {
        'users',
        'users_support',
        'user_activity',
        'configuration',
    }
    assert result.synchronization.users_projected is True
    assert result.synchronization.navigation_projected is True
    print('R18C prepare completed.')
    print(f"Cosmos database: {os.environ['ATLANTICUS_COSMOS_DATABASE']}")
    print(f"SharePoint root: {os.environ['ATLANTICUS_SHAREPOINT_ROOT_PATH']}")


def _user() -> UserConfiguration:
    return UserConfiguration.create(
        display_name=_DISPLAY_NAME,
        email=_EMAIL,
        profile_key=_PROFILE_KEY,
        issuer=f'app_service:aad:tenant:{_TENANT_ID}',
        subject_id=_SUBJECT_ID,
    )


def _encode(value: bytes) -> str:
    return base64.b64encode(value).decode('ascii')


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


if __name__ == '__main__':
    main()
