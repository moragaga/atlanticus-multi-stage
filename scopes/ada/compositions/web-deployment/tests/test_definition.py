import pytest

from ada.compositions.web_bootstrap import AdaConfigurationFilenames, AdaCosmosBindings
from ada.compositions.web_deployment import AdaWebDeploymentDefinition, AdaWebDeploymentError
from atlanticus.web.compositions.runtime_infrastructure import (
    CosmosConnectionEnvironmentDefinition,
    SharePointEnvironmentDefinition,
)


def _cosmos(name: str) -> CosmosConnectionEnvironmentDefinition:
    prefix = name.upper().replace('-', '_')
    return CosmosConnectionEnvironmentDefinition(
        name=name,
        endpoint_variable=f'{prefix}_ENDPOINT',
        key_variable=f'{prefix}_KEY',
        database_name_variable=f'{prefix}_DATABASE',
    )


def _sharepoint() -> SharePointEnvironmentDefinition:
    return SharePointEnvironmentDefinition(
        read_endpoint_variable='SHAREPOINT_READ',
        write_endpoint_variable='SHAREPOINT_WRITE',
        root_path_variable='SHAREPOINT_ROOT',
        tool_path_variable='SHAREPOINT_TOOL',
    )


def test_definition_accepts_arbitrary_solution_connection_names() -> None:
    definition = AdaWebDeploymentDefinition(
        cosmos_connections=(_cosmos('configuration-store'), _cosmos('activity-store')),
        bindings=AdaCosmosBindings(
            users='configuration-store',
            navigation='configuration-store',
            tools='configuration-store',
            activity='activity-store',
        ),
        sharepoint=_sharepoint(),
    )

    assert tuple(item.name for item in definition.cosmos_connections) == (
        'configuration-store',
        'activity-store',
    )


def test_definition_rejects_binding_to_unknown_connection() -> None:
    with pytest.raises(AdaWebDeploymentError, match="capability 'activity'.*'missing'"):
        AdaWebDeploymentDefinition(
            cosmos_connections=(_cosmos('application'),),
            bindings=AdaCosmosBindings(
                users='application',
                navigation='application',
                tools='application',
                activity='missing',
            ),
            sharepoint=_sharepoint(),
        )


def test_definition_rejects_duplicate_connection_names() -> None:
    with pytest.raises(AdaWebDeploymentError, match='Cosmos connection names must be unique'):
        AdaWebDeploymentDefinition(
            cosmos_connections=(_cosmos('application'), _cosmos('application')),
            bindings=AdaCosmosBindings(
                users='application',
                navigation='application',
                tools='application',
                activity='application',
            ),
            sharepoint=_sharepoint(),
        )


def test_definition_accepts_runtime_selected_configuration_filenames() -> None:
    definition = AdaWebDeploymentDefinition(
        cosmos_connections=(
            CosmosConnectionEnvironmentDefinition(
                name='application',
                endpoint_variable='COSMOS_ENDPOINT',
                key_variable='COSMOS_KEY',
                database_name_variable='COSMOS_DATABASE',
            ),
        ),
        bindings=AdaCosmosBindings(
            users='application',
            activity='application',
            navigation='application',
            tools='application',
        ),
        sharepoint=SharePointEnvironmentDefinition(
            read_endpoint_variable='SP_READ',
            write_endpoint_variable='SP_WRITE',
            root_path_variable='SP_ROOT',
            tool_path_variable='SP_TOOL',
        ),
        configuration_filenames=AdaConfigurationFilenames(
            users='__e2e_users.json.gz',
            navigation='__e2e_navigation.json.gz',
            tools='__e2e_tools.json.gz',
        ),
    )

    assert definition.configuration_filenames.users == '__e2e_users.json.gz'
