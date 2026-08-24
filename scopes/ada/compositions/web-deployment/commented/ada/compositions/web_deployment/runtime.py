from __future__ import annotations

from ada.compositions.web_bootstrap import AdaRuntimeProjection, create_ada_web_bootstrap
from ada.compositions.web_deployment.access import (
    resolve_bootstrap_admin_principal,
    resolve_deployment_environment,
)
from ada.compositions.web_deployment.models import (
    AdaWebDeploymentDefinition,
    AdaWebDeploymentRuntime,
)
from atlanticus.web.compositions.runtime_infrastructure import (
    SharePointInfrastructureSettings,
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
    runtime_projection: AdaRuntimeProjection | None = None,
    sharepoint: SharePointInfrastructureSettings | None = None,
) -> AdaWebDeploymentRuntime:
    if not isinstance(definition, AdaWebDeploymentDefinition):
        raise TypeError('definition must be AdaWebDeploymentDefinition')
    if sharepoint is not None and not isinstance(sharepoint, SharePointInfrastructureSettings):
        raise TypeError('sharepoint must be SharePointInfrastructureSettings or None')
    reader = _environment_reader(environment)
    web_environment = resolve_deployment_environment(reader)
    bootstrap_admin_principal = resolve_bootstrap_admin_principal(reader, web_environment)
    # Cosmos siempre forma parte del runtime ADA.
    # SharePoint se agrega sólo si el composition root lo pide.
    connections = resolve_cosmos_connections(reader, definition.cosmos_connections)
    infrastructure = WebRuntimeInfrastructure(
        cosmos_connections=connections,
        sharepoint=sharepoint,
    )
    # Un único lifecycle abre todos los recursos compartidos configurados para este worker.
    infrastructure.open()
    try:
        bootstrap = create_ada_web_bootstrap(
            metadata=metadata,
            environment=web_environment,
            bootstrap_admin_principal=bootstrap_admin_principal,
            infrastructure=infrastructure,
            bindings=definition.bindings,
            users_runtime=users_runtime,
            runtime_projection=runtime_projection,
        )
        return AdaWebDeploymentRuntime(
            infrastructure=infrastructure,
            bootstrap=bootstrap,
        )
    except Exception:
        # Si Bootstrap falla, el mismo owner libera Cosmos y SharePoint en conjunto.
        _close_quietly(infrastructure)
        raise


def _environment_reader(environment: EnvironmentReader | None) -> EnvironmentReader:
    if environment is None:
        return EnvironmentReader()
    if not isinstance(environment, EnvironmentReader):
        raise TypeError('environment must be EnvironmentReader or None')
    return environment


def _close_quietly(infrastructure: WebRuntimeInfrastructure) -> None:
    # El cleanup de error no debe ocultar la excepción de startup original.
    try:
        infrastructure.close()
    except Exception:
        return
