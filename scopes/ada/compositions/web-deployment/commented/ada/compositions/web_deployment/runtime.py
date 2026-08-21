# El runtime operacional resuelve solo la infraestructura Cosmos requerida por la aplicación.
from __future__ import annotations

from ada.compositions.web_bootstrap import create_ada_web_bootstrap
from ada.compositions.web_deployment.access import (
    resolve_bootstrap_admin_principal,
    resolve_deployment_environment,
)
from ada.compositions.web_deployment.models import (
    AdaWebDeploymentDefinition,
    AdaWebDeploymentRuntime,
)
from atlanticus.web.compositions.runtime_infrastructure import (
    WebRuntimeInfrastructure,
    resolve_cosmos_connections,
)
from atlanticus.web.environment import EnvironmentReader
from atlanticus.web.models import ApplicationMetadata
from atlanticus.web.users.runtime import UsersRuntime


def open_ada_web_deployment_runtime(
    *,
    definition: AdaWebDeploymentDefinition,
    metadata: ApplicationMetadata,
    environment: EnvironmentReader | None = None,
    users_runtime: UsersRuntime | None = None,
) -> AdaWebDeploymentRuntime:
    # Valida el contrato de deployment antes de resolver infraestructura.
    if not isinstance(definition, AdaWebDeploymentDefinition):
        raise TypeError('definition must be AdaWebDeploymentDefinition')
    reader = _environment_reader(environment)
    web_environment = resolve_deployment_environment(reader)
    bootstrap_admin_principal = resolve_bootstrap_admin_principal(reader, web_environment)
    connections = resolve_cosmos_connections(reader, definition.cosmos_connections)

    # El worker operacional abre únicamente clientes Cosmos de larga vida.
    infrastructure = WebRuntimeInfrastructure(cosmos_connections=connections)
    infrastructure.open()
    try:
        bootstrap = create_ada_web_bootstrap(
            metadata=metadata,
            environment=web_environment,
            bootstrap_admin_principal=bootstrap_admin_principal,
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
    # Reutiliza el reader inyectado en tests/composición o crea el reader del proceso.
    if environment is None:
        return EnvironmentReader()
    if not isinstance(environment, EnvironmentReader):
        raise TypeError('environment must be EnvironmentReader or None')
    return environment


def _close_quietly(infrastructure: WebRuntimeInfrastructure) -> None:
    # El cierre de recuperación no oculta el error original de bootstrap.
    try:
        infrastructure.close()
    except Exception:
        return
