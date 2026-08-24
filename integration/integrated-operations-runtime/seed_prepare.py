from __future__ import annotations

import base64
import os
import time
from dataclasses import replace
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from ada.compositions.web_bootstrap import create_ada_configuration_backends
from ada.compositions.web_deployment import prepare_ada_web_deployment
from ada.configuration.tools import (
    ToolConfigurationBundle,
    ToolConfigurationCatalog,
    ToolProjectionWorkflow,
    integrated_operations_configuration_from_manifest,
)
from ada.configuration.tools.adapters import (
    SharePointToolConfigurationSettings,
    SharePointToolConfigurationStore,
)
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from atlanticus.web.compositions.runtime_infrastructure import (
    WebRuntimeInfrastructure,
    resolve_cosmos_connections,
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
    UserConfiguration,
    UserProfileConfiguration,
    UsersConfigurationBundle,
    UsersConfigurationCatalog,
    UsersConfigurationSourceDocument,
    encode_users_configuration_source,
)
from integrated_operations.deployment.definition import build_deployment_definition

_READY_TIMEOUT_SECONDS = 120.0
_READY_INTERVAL_SECONDS = 1.0
_PROFILE_KEY = 'operator'
_TENANT_ID = '00000000-0000-0000-0000-000000000018'
_SUBJECT_ID = '00000000-0000-0000-0000-000000000043'
_EMAIL = 'atlanticus.r18c@example.com'
_DISPLAY_NAME = 'Atlanticus R18C Operator'
_PROJECTED_MILL_DISPLAY_NAME = 'Molienda proyectada R19B2'


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
            saved_by='ada-r19b2-smoke',
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
            saved_by='ada-r19b2-smoke',
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
        tool_bundle = _publish_tool_source(
            gateway=gateway,
            filename=definition.configuration_filenames.tools,
            relative_path=paths.tool_relative_path,
        )
    finally:
        infrastructure.close()

    result = prepare_ada_web_deployment(
        definition=definition,
        environment=environment,
        create_databases_if_missing=True,
        actor='ada-r19b2-smoke',
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
    _project_tools(
        environment=environment,
        definition=definition,
        sharepoint_settings=sharepoint_settings,
        source_revision=tool_bundle.revision,
    )
    print('R19B2 prepare completed.')
    print(f'Cosmos database: {os.environ["ATLANTICUS_COSMOS_DATABASE"]}')
    print(f'SharePoint root: {os.environ["ATLANTICUS_SHAREPOINT_ROOT_PATH"]}')
    print(f'Tool projection source revision: {tool_bundle.revision}')


def _publish_tool_source(*, gateway, filename: str, relative_path: str) -> ToolConfigurationBundle:
    base = integrated_operations_configuration_from_manifest(INTEGRATED_OPERATIONS_MANIFEST)
    components = tuple(
        replace(component, display_name=_PROJECTED_MILL_DISPLAY_NAME)
        if component.key == 'molienda'
        else component
        for component in base.components
    )
    catalog = ToolConfigurationCatalog((replace(base, components=components),))
    bundle = ToolConfigurationBundle.create(catalog=catalog, saved_by='ada-r19b2-smoke')
    store = SharePointToolConfigurationStore(
        gateway=gateway,
        settings=SharePointToolConfigurationSettings(
            filename=filename,
            relative_path=relative_path,
        ),
    )
    current = store.fetch_bundle()
    store.publish_bundle(
        bundle,
        expected_source_revision=current.revision if current is not None else None,
    )
    return bundle


def _project_tools(*, environment, definition, sharepoint_settings, source_revision: str) -> None:
    connections = resolve_cosmos_connections(environment, definition.cosmos_connections)
    infrastructure = WebRuntimeInfrastructure(
        cosmos_connections=connections,
        sharepoint=sharepoint_settings,
    )
    infrastructure.open()
    try:
        configuration = create_ada_configuration_backends(
            infrastructure=infrastructure,
            bindings=definition.bindings,
            filenames=definition.configuration_filenames,
        )
        result = ToolProjectionWorkflow(
            source=configuration.tools_source,
            projection=configuration.tools_projection,
            audit_actor_provider=lambda: 'ada-r19b2-smoke',
        ).project(source_revision)
        assert result.projected is True
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
