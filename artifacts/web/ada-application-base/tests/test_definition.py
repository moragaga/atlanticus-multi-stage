import pytest

from ada_application_base.definition import (
    build_deployment_definition,
    build_flask_config,
    build_metadata,
)
from atlanticus.web.environment import EnvironmentReader
from atlanticus.web.errors import WebConfigurationError


def test_metadata_is_stable() -> None:
    metadata = build_metadata()

    assert metadata.application_id == 'ada-application-base'
    assert metadata.display_name == 'ADA'
    assert metadata.version == '0.2.4'


def test_deployment_definition_binds_all_ada_capabilities_to_application_connection() -> None:
    definition = build_deployment_definition(EnvironmentReader({}))

    assert len(definition.cosmos_connections) == 1
    connection = definition.cosmos_connections[0]
    assert connection.name == 'application'
    assert connection.endpoint_variable == 'ATLANTICUS_COSMOS_ENDPOINT'
    assert connection.key_variable == 'ATLANTICUS_COSMOS_KEY'
    assert connection.database_name_variable == 'ATLANTICUS_COSMOS_DATABASE'
    assert connection.allow_insecure_http is False
    assert definition.bindings.users == 'application'
    assert definition.bindings.activity == 'application'
    assert definition.bindings.navigation == 'application'
    assert definition.bindings.tools == 'application'


def test_cosmos_insecure_http_requires_explicit_deployment_opt_in() -> None:
    definition = build_deployment_definition(
        EnvironmentReader({'ATLANTICUS_COSMOS_ALLOW_INSECURE_HTTP': 'true'})
    )

    assert definition.cosmos_connections[0].allow_insecure_http is True


def test_invalid_cosmos_insecure_http_value_is_rejected() -> None:
    with pytest.raises(
        WebConfigurationError,
        match='ATLANTICUS_COSMOS_ALLOW_INSECURE_HTTP',
    ):
        build_deployment_definition(
            EnvironmentReader({'ATLANTICUS_COSMOS_ALLOW_INSECURE_HTTP': 'sometimes'})
        )


def test_sharepoint_definition_uses_existing_deployment_environment_contract() -> None:
    sharepoint = build_deployment_definition(EnvironmentReader({})).sharepoint

    assert sharepoint.read_endpoint_variable == 'ATLANTICUS_SHAREPOINT_READ_ENDPOINT'
    assert sharepoint.write_endpoint_variable == 'ATLANTICUS_SHAREPOINT_WRITE_ENDPOINT'
    assert sharepoint.root_path_variable == 'ATLANTICUS_SHAREPOINT_ROOT_PATH'
    assert sharepoint.tool_path_variable == 'ATLANTICUS_SHAREPOINT_TOOL_PATH'
    assert sharepoint.allow_insecure_http is False


def test_flask_config_maps_session_secret_from_environment() -> None:
    config = build_flask_config(
        EnvironmentReader({'ATLANTICUS_FLASK_SECRET_KEY': 'session-secret'})
    )

    assert config == {'SECRET_KEY': 'session-secret'}


def test_flask_config_does_not_invent_session_secret() -> None:
    assert build_flask_config(EnvironmentReader({})) == {}
