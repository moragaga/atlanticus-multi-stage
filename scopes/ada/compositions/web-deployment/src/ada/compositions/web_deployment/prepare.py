from __future__ import annotations

from ada.compositions.web_bootstrap import (
    create_ada_configuration_backends,
    ensure_ada_cosmos_infrastructure,
    synchronize_ada_access_projections,
)
from ada.compositions.web_deployment.models import (
    AdaWebDeploymentDefinition,
    AdaWebPreparationResult,
)
from atlanticus.web.compositions.runtime_infrastructure import (
    WebRuntimeInfrastructure,
    resolve_cosmos_connections,
    resolve_sharepoint_infrastructure_settings,
)
from atlanticus.web.environment import EnvironmentReader


def prepare_ada_web_deployment(
    *,
    definition: AdaWebDeploymentDefinition,
    environment: EnvironmentReader | None = None,
    create_databases_if_missing: bool = False,
    actor: str = 'ada-bootstrap',
) -> AdaWebPreparationResult:
    if not isinstance(definition, AdaWebDeploymentDefinition):
        raise TypeError('definition must be AdaWebDeploymentDefinition')
    if not isinstance(create_databases_if_missing, bool):
        raise TypeError('create_databases_if_missing must be a boolean')
    reader = _environment_reader(environment)
    connections = resolve_cosmos_connections(reader, definition.cosmos_connections)
    sharepoint = resolve_sharepoint_infrastructure_settings(reader, definition.sharepoint)
    provisioning = ensure_ada_cosmos_infrastructure(
        cosmos_connections=connections,
        bindings=definition.bindings,
        create_databases_if_missing=create_databases_if_missing,
    )
    infrastructure = WebRuntimeInfrastructure(
        cosmos_connections=connections,
        sharepoint=sharepoint,
    )
    infrastructure.open()
    try:
        configuration = create_ada_configuration_backends(
            infrastructure=infrastructure,
            bindings=definition.bindings,
            filenames=definition.configuration_filenames,
        )
        synchronization = synchronize_ada_access_projections(
            configuration=configuration,
            actor=actor,
        )
    finally:
        infrastructure.close()
    return AdaWebPreparationResult(
        provisioning=provisioning,
        synchronization=synchronization,
    )


def _environment_reader(environment: EnvironmentReader | None) -> EnvironmentReader:
    if environment is None:
        return EnvironmentReader()
    if not isinstance(environment, EnvironmentReader):
        raise TypeError('environment must be EnvironmentReader or None')
    return environment
