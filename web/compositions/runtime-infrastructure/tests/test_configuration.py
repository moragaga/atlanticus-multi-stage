from types import MappingProxyType

import pytest

from atlanticus.web.compositions.runtime_infrastructure import (
    CosmosConnectionEnvironmentDefinition,
    SharePointEnvironmentDefinition,
    resolve_cosmos_connections,
    resolve_sharepoint_infrastructure_settings,
)
from atlanticus.web.environment import EnvironmentReader


def test_cosmos_connections_are_resolved_from_explicit_variable_names() -> None:
    reader = EnvironmentReader(
        {
            'ADA_PRIMARY_ENDPOINT': 'https://primary.documents.azure.com',
            'ADA_PRIMARY_KEY': 'primary-secret',
            'ADA_PRIMARY_DATABASE': 'ada-primary',
            'ADA_HISTORY_ENDPOINT': 'https://history.documents.azure.com/',
            'ADA_HISTORY_KEY': 'history-secret',
            'ADA_HISTORY_DATABASE': 'ada-history',
        }
    )

    connections = resolve_cosmos_connections(
        reader,
        (
            CosmosConnectionEnvironmentDefinition(
                name='application',
                endpoint_variable='ADA_PRIMARY_ENDPOINT',
                key_variable='ADA_PRIMARY_KEY',
                database_name_variable='ADA_PRIMARY_DATABASE',
            ),
            CosmosConnectionEnvironmentDefinition(
                name='history',
                endpoint_variable='ADA_HISTORY_ENDPOINT',
                key_variable='ADA_HISTORY_KEY',
                database_name_variable='ADA_HISTORY_DATABASE',
            ),
        ),
    )

    assert isinstance(connections, MappingProxyType)
    assert tuple(connections) == ('application', 'history')
    assert connections['application'].endpoint == 'https://primary.documents.azure.com'
    assert connections['application'].database_name == 'ada-primary'
    assert connections['history'].database_name == 'ada-history'
    assert 'primary-secret' not in repr(connections['application'])


def test_cosmos_connection_names_are_solution_defined_and_duplicates_are_rejected() -> None:
    definition = CosmosConnectionEnvironmentDefinition(
        name='anything-the-solution-needs',
        endpoint_variable='ENDPOINT',
        key_variable='KEY',
        database_name_variable='DATABASE',
    )
    reader = EnvironmentReader(
        {
            'ENDPOINT': 'https://example.documents.azure.com/',
            'KEY': 'secret',
            'DATABASE': 'example',
        }
    )

    with pytest.raises(ValueError, match='Duplicate Cosmos connection definition'):
        resolve_cosmos_connections(reader, (definition, definition))


def test_cosmos_local_http_is_explicit_and_not_inferred_from_an_environment_mode() -> None:
    reader = EnvironmentReader(
        {
            'ENDPOINT': 'http://cosmos-emulator:8081',
            'KEY': 'emulator-key',
            'DATABASE': 'ada-local',
        }
    )
    definition = CosmosConnectionEnvironmentDefinition(
        name='local-test',
        endpoint_variable='ENDPOINT',
        key_variable='KEY',
        database_name_variable='DATABASE',
        allow_insecure_http=True,
    )

    connections = resolve_cosmos_connections(reader, (definition,))

    assert connections['local-test'].endpoint == 'http://cosmos-emulator:8081'
    assert connections['local-test'].allow_insecure_http is True


def test_sharepoint_settings_use_declared_variables_and_split_signed_endpoints() -> None:
    definition = SharePointEnvironmentDefinition(
        read_endpoint_variable='SP_READ',
        write_endpoint_variable='SP_WRITE',
        root_path_variable='SP_ROOT',
        tool_path_variable='SP_TOOL',
    )
    reader = EnvironmentReader(
        {
            'SP_READ': 'https://power.example.com:443/read/invoke?api-version=1&sig=read-secret',
            'SP_WRITE': (
                'https://power.example.com:443/write/invoke?api-version=1&sig=write-secret'
            ),
            'SP_ROOT': 'conciencia_situacional',
            'SP_TOOL': 'operaciones_integradas',
        }
    )

    settings = resolve_sharepoint_infrastructure_settings(reader, definition)

    assert settings.http.base_url == 'https://power.example.com:443/'
    assert settings.gateway.read_endpoint == 'read/invoke'
    assert settings.gateway.write_endpoint == 'write/invoke'
    assert dict(settings.gateway.read_parameters) == {
        'api-version': '1',
        'sig': 'read-secret',
    }
    assert dict(settings.gateway.write_parameters) == {
        'api-version': '1',
        'sig': 'write-secret',
    }
    assert settings.paths.users_relative_path == 'conciencia_situacional/users'
    assert (
        settings.paths.navigation_relative_path
        == 'conciencia_situacional/operaciones_integradas/navigation'
    )
    assert settings.paths.tool_relative_path == 'conciencia_situacional/operaciones_integradas/tool'
    assert 'read-secret' not in repr(settings.gateway)
    assert 'write-secret' not in repr(settings.gateway)


def test_sharepoint_endpoints_must_share_one_http_client_origin() -> None:
    definition = SharePointEnvironmentDefinition(
        read_endpoint_variable='READ',
        write_endpoint_variable='WRITE',
        root_path_variable='ROOT',
        tool_path_variable='TOOL',
    )
    reader = EnvironmentReader(
        {
            'READ': 'https://read.example.com/invoke?sig=a',
            'WRITE': 'https://write.example.com/invoke?sig=b',
            'ROOT': 'root',
            'TOOL': 'tool',
        }
    )

    with pytest.raises(
        ValueError,
        match='SharePoint Power Automate endpoints must share the same origin',
    ):
        resolve_sharepoint_infrastructure_settings(reader, definition)


def test_environment_definitions_do_not_require_fixed_atlanticus_variable_names() -> None:
    cosmos = CosmosConnectionEnvironmentDefinition(
        name='projection',
        endpoint_variable='CUSTOM_ENDPOINT',
        key_variable='CUSTOM_SECRET',
        database_name_variable='CUSTOM_DATABASE',
    )
    sharepoint = SharePointEnvironmentDefinition(
        read_endpoint_variable='READ_URL',
        write_endpoint_variable='WRITE_URL',
        root_path_variable='ROOT_FOLDER',
        tool_path_variable='TOOL_FOLDER',
    )

    assert cosmos.endpoint_variable == 'CUSTOM_ENDPOINT'
    assert cosmos.database_name_variable == 'CUSTOM_DATABASE'
    assert sharepoint.root_path_variable == 'ROOT_FOLDER'
