from __future__ import annotations

import base64
import os
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from urllib.parse import parse_qsl, urlsplit, urlunsplit

from ada.configuration.tools import (
    ToolConfigurationBundle,
    integrated_operations_configuration_from_manifest,
)
from ada.configuration.tools.adapters import (
    SharePointToolConfigurationSettings,
    SharePointToolConfigurationStore,
)
from ada.configuration.tools.bundle import (
    ToolConfigurationSourceDocument,
    encode_tool_configuration_source,
)
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from atlanticus.connectivity.http import HttpAuthMode, HttpClient, HttpSettings
from atlanticus.web.compositions.sharepoint_http import (
    PowerAutomateSharePointGateway,
    PowerAutomateSharePointSettings,
    SharePointPathSettings,
)
from atlanticus.web.navigation.configuration import (
    NavigationConfigurationBundle,
    NavigationConfigurationCatalog,
    NavigationConfigurationSourceDocument,
    NavigationLinkConfiguration,
    encode_navigation_configuration_source,
)
from atlanticus.web.navigation.configuration.adapters import (
    SharePointNavigationConfigurationSettings,
    SharePointNavigationConfigurationStore,
)
from atlanticus.web.users.configuration import (
    UsersConfigurationBundle,
    UsersConfigurationCatalog,
    UsersConfigurationSourceDocument,
    encode_users_configuration_source,
)
from atlanticus.web.users.configuration.adapters import (
    SharePointUsersConfigurationSettings,
    SharePointUsersConfigurationStore,
)


@dataclass(frozen=True, slots=True)
class _HttpTarget:
    base_url: str
    endpoint: str
    parameters: Mapping[str, str] = field(repr=False)


def test_sharepoint_power_automate_end_to_end() -> None:
    read_target = _parse_target(_required_environment('ATLANTICUS_SHAREPOINT_READ_ENDPOINT'))
    write_target = _parse_target(_required_environment('ATLANTICUS_SHAREPOINT_WRITE_ENDPOINT'))
    if read_target.base_url != write_target.base_url:
        raise RuntimeError('Power Automate read and write endpoints must share the same origin')

    paths = SharePointPathSettings(
        root_path=_required_environment('ATLANTICUS_SHAREPOINT_ROOT_PATH'),
        tool_path=_required_environment('ATLANTICUS_SHAREPOINT_TOOL_PATH'),
    )
    client = HttpClient(
        settings=HttpSettings(
            base_url=read_target.base_url,
            auth_mode=HttpAuthMode.NONE,
        )
    )
    gateway = PowerAutomateSharePointGateway(
        client=client,
        settings=PowerAutomateSharePointSettings(
            read_endpoint=read_target.endpoint,
            write_endpoint=write_target.endpoint,
            read_parameters=read_target.parameters,
            write_parameters=write_target.parameters,
        ),
    )
    try:
        _exercise_binary_round_trip(gateway, paths=paths)
        _exercise_users_store(gateway, paths=paths)
        _exercise_navigation_store(gateway, paths=paths)
        _exercise_tool_store(gateway, paths=paths)
        print(f'SharePoint root: {paths.root_path}')
        print(f'SharePoint tool: {paths.tool_path}')
        print(f'Users path: {paths.users_relative_path}')
        print(f'Navigation path: {paths.navigation_relative_path}')
        print(f'Tool path: {paths.tool_relative_path}')
    finally:
        client.close()


def _exercise_binary_round_trip(
    gateway: PowerAutomateSharePointGateway,
    *,
    paths: SharePointPathSettings,
) -> None:
    filename = '__atlanticus_e2e_roundtrip.bin'
    first = b'atlanticus-sharepoint-e2e-v1\x00\xff'
    second = b'atlanticus-sharepoint-e2e-v2\x00\x01\xfe\xff'
    gateway.write(
        filename=filename,
        relative_path=paths.integration_relative_path,
        content=_encode(first),
    )
    assert (
        _decode(gateway.read(filename=filename, relative_path=paths.integration_relative_path))
        == first
    )
    gateway.write(
        filename=filename,
        relative_path=paths.integration_relative_path,
        content=_encode(second),
    )
    assert (
        _decode(gateway.read(filename=filename, relative_path=paths.integration_relative_path))
        == second
    )


def _exercise_users_store(
    gateway: PowerAutomateSharePointGateway,
    *,
    paths: SharePointPathSettings,
) -> None:
    filename = '__atlanticus_e2e_users_configuration.json.gz'
    first = UsersConfigurationBundle.create(
        catalog=UsersConfigurationCatalog(
            administrator_background_color='#673AB7',
            guest_background_color='#FF5722',
        ),
        saved_by='sharepoint-e2e',
    )
    second = UsersConfigurationBundle.create(
        catalog=UsersConfigurationCatalog(
            administrator_background_color='#512DA8',
            guest_background_color='#F4511E',
        ),
        saved_by='sharepoint-e2e',
    )
    gateway.write(
        filename=filename,
        relative_path=paths.users_relative_path,
        content=_encode_source(
            encode_users_configuration_source,
            UsersConfigurationSourceDocument.from_bundle(first),
        ),
    )
    store = SharePointUsersConfigurationStore(
        gateway=gateway,
        settings=SharePointUsersConfigurationSettings(
            filename=filename,
            relative_path=paths.users_relative_path,
        ),
    )
    assert store.fetch_bundle() == first
    store.publish_bundle(second)
    assert store.fetch_bundle() == second
    assert store.fetch_revision(first.revision) == first


def _exercise_navigation_store(
    gateway: PowerAutomateSharePointGateway,
    *,
    paths: SharePointPathSettings,
) -> None:
    filename = '__atlanticus_e2e_navigation_configuration.json.gz'
    first = NavigationConfigurationBundle.create(
        catalog=NavigationConfigurationCatalog(
            links=(NavigationLinkConfiguration(key='home', label='Home', href='/'),),
        ),
        saved_by='sharepoint-e2e',
    )
    second = NavigationConfigurationBundle.create(
        catalog=NavigationConfigurationCatalog(
            links=(NavigationLinkConfiguration(key='home', label='Inicio', href='/'),),
        ),
        saved_by='sharepoint-e2e',
    )
    gateway.write(
        filename=filename,
        relative_path=paths.navigation_relative_path,
        content=_encode_source(
            encode_navigation_configuration_source,
            NavigationConfigurationSourceDocument.from_bundle(first),
        ),
    )
    store = SharePointNavigationConfigurationStore(
        gateway=gateway,
        settings=SharePointNavigationConfigurationSettings(
            filename=filename,
            relative_path=paths.navigation_relative_path,
        ),
    )
    assert store.fetch_bundle() == first
    store.publish_bundle(second)
    assert store.fetch_bundle() == second
    assert store.fetch_revision(first.revision) == first


def _exercise_tool_store(
    gateway: PowerAutomateSharePointGateway,
    *,
    paths: SharePointPathSettings,
) -> None:
    filename = '__atlanticus_e2e_tool_configuration.json.gz'
    tool = integrated_operations_configuration_from_manifest(INTEGRATED_OPERATIONS_MANIFEST)
    first = ToolConfigurationBundle.create(
        configuration=tool,
        saved_by='sharepoint-e2e',
    )
    second = ToolConfigurationBundle.create(
        configuration=replace(tool, display_name='Operaciones Integradas E2E'),
        saved_by='sharepoint-e2e',
    )
    gateway.write(
        filename=filename,
        relative_path=paths.tool_relative_path,
        content=_encode_source(
            encode_tool_configuration_source,
            ToolConfigurationSourceDocument.from_bundle(first),
        ),
    )
    store = SharePointToolConfigurationStore(
        gateway=gateway,
        settings=SharePointToolConfigurationSettings(
            filename=filename,
            relative_path=paths.tool_relative_path,
        ),
    )
    assert store.fetch_bundle() == first
    store.publish_bundle(second)
    assert store.fetch_bundle() == second
    assert store.fetch_revision(first.revision) == first


def _parse_target(value: str) -> _HttpTarget:
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.hostname is None:
        raise RuntimeError('Power Automate endpoint must be an absolute HTTPS URL')
    if parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise RuntimeError('Power Automate endpoint URL is invalid')
    parameters = dict(parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True))
    return _HttpTarget(
        base_url=urlunsplit((parsed.scheme, parsed.netloc, '/', '', '')),
        endpoint=parsed.path.lstrip('/'),
        parameters=MappingProxyType(parameters),
    )


def _required_environment(name: str) -> str:
    value = os.getenv(name, '').strip()
    if not value:
        raise RuntimeError(f'{name} is required')
    return value


def _encode(value: bytes) -> str:
    return base64.b64encode(value).decode('ascii')


def _decode(value: str | None) -> bytes:
    if value is None:
        raise AssertionError('SharePoint read returned no content')
    return base64.b64decode(value, validate=True)


def _encode_source(encoder: object, source: object) -> str:
    if not callable(encoder):
        raise TypeError('encoder must be callable')
    payload = encoder(source)
    if not isinstance(payload, bytes):
        raise TypeError('source encoder must return bytes')
    return _encode(payload)
