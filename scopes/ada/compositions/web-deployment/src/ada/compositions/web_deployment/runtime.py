from __future__ import annotations

from ada.compositions.web_bootstrap import create_ada_web_bootstrap
from ada.compositions.web_deployment.models import (
    AdaWebDeploymentDefinition,
    AdaWebDeploymentRuntime,
)
from atlanticus.web.compositions.runtime_infrastructure import (
    WebRuntimeInfrastructure,
    resolve_cosmos_connections,
)
from atlanticus.web.environment import EnvironmentReader
from atlanticus.web.identity.provider import IdentityProvider
from atlanticus.web.models import ApplicationMetadata
from atlanticus.web.users.runtime import UsersRuntime


def open_ada_web_deployment_runtime(
    *,
    definition: AdaWebDeploymentDefinition,
    metadata: ApplicationMetadata,
    identity_provider: IdentityProvider,
    environment: EnvironmentReader | None = None,
    users_runtime: UsersRuntime | None = None,
) -> AdaWebDeploymentRuntime:
    if not isinstance(definition, AdaWebDeploymentDefinition):
        raise TypeError('definition must be AdaWebDeploymentDefinition')
    reader = _environment_reader(environment)
    connections = resolve_cosmos_connections(reader, definition.cosmos_connections)
    infrastructure = WebRuntimeInfrastructure(cosmos_connections=connections)
    infrastructure.open()
    try:
        bootstrap = create_ada_web_bootstrap(
            metadata=metadata,
            identity_provider=identity_provider,
            infrastructure=infrastructure,
            bindings=definition.bindings,
            users_runtime=users_runtime,
        )
        return AdaWebDeploymentRuntime(
            infrastructure=infrastructure,
            bootstrap=bootstrap,
        )
    except Exception:
        _close_quietly(infrastructure)
        raise


def _environment_reader(environment: EnvironmentReader | None) -> EnvironmentReader:
    if environment is None:
        return EnvironmentReader()
    if not isinstance(environment, EnvironmentReader):
        raise TypeError('environment must be EnvironmentReader or None')
    return environment


def _close_quietly(infrastructure: WebRuntimeInfrastructure) -> None:
    try:
        infrastructure.close()
    except Exception:
        return
