# Define la identidad versionada del artifact ADA que incorpora el lifecycle explícito del workspace del Manager.
# El espejo conserva exactamente el comportamiento productivo y agrega solo contexto pedagógico.

from ada.compositions.web_bootstrap import AdaCosmosBindings
from ada.compositions.web_deployment import AdaWebDeploymentDefinition
from atlanticus.web.compositions.runtime_infrastructure import (
    CosmosConnectionEnvironmentDefinition,
    SharePointEnvironmentDefinition,
)
from atlanticus.web.environment import EnvironmentReader
from atlanticus.web.errors import WebConfigurationError
from atlanticus.web.models import ApplicationMetadata

_APPLICATION_CONNECTION = 'application'
_COSMOS_ALLOW_INSECURE_HTTP_VARIABLE = 'ATLANTICUS_COSMOS_ALLOW_INSECURE_HTTP'
_FLASK_SECRET_KEY_VARIABLE = 'ATLANTICUS_FLASK_SECRET_KEY'
_TRUE_VALUES = frozenset({'1', 'true', 'yes', 'on'})
_FALSE_VALUES = frozenset({'0', 'false', 'no', 'off'})


def build_metadata() -> ApplicationMetadata:
    return ApplicationMetadata(
        application_id='ada-application-base',
        display_name='ADA',
        version='0.2.6',
    )


def build_deployment_definition(
    environment: EnvironmentReader | None = None,
) -> AdaWebDeploymentDefinition:
    reader = _environment_reader(environment)
    return AdaWebDeploymentDefinition(
        cosmos_connections=(
            CosmosConnectionEnvironmentDefinition(
                name=_APPLICATION_CONNECTION,
                endpoint_variable='ATLANTICUS_COSMOS_ENDPOINT',
                key_variable='ATLANTICUS_COSMOS_KEY',
                database_name_variable='ATLANTICUS_COSMOS_DATABASE',
                allow_insecure_http=_optional_boolean(
                    reader,
                    _COSMOS_ALLOW_INSECURE_HTTP_VARIABLE,
                    default=False,
                ),
            ),
        ),
        bindings=AdaCosmosBindings(
            users=_APPLICATION_CONNECTION,
            activity=_APPLICATION_CONNECTION,
            navigation=_APPLICATION_CONNECTION,
            tools=_APPLICATION_CONNECTION,
        ),
        sharepoint=SharePointEnvironmentDefinition(
            read_endpoint_variable='ATLANTICUS_SHAREPOINT_READ_ENDPOINT',
            write_endpoint_variable='ATLANTICUS_SHAREPOINT_WRITE_ENDPOINT',
            root_path_variable='ATLANTICUS_SHAREPOINT_ROOT_PATH',
            tool_path_variable='ATLANTICUS_SHAREPOINT_TOOL_PATH',
        ),
    )


def build_flask_config(
    environment: EnvironmentReader | None = None,
) -> dict[str, object]:
    reader = _environment_reader(environment)
    secret_key = reader.optional(_FLASK_SECRET_KEY_VARIABLE)
    if secret_key is None or secret_key == '':
        return {}
    return {'SECRET_KEY': secret_key}


def _environment_reader(environment: EnvironmentReader | None) -> EnvironmentReader:
    if environment is None:
        return EnvironmentReader()
    if not isinstance(environment, EnvironmentReader):
        raise TypeError('environment must be EnvironmentReader or None')
    return environment


def _optional_boolean(
    environment: EnvironmentReader,
    variable_name: str,
    *,
    default: bool,
) -> bool:
    value = environment.optional(variable_name)
    if value is None or value == '':
        return default
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise WebConfigurationError(f'Invalid {variable_name}: expected true or false')
