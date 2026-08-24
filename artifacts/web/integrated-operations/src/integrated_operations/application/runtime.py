from __future__ import annotations

from dataclasses import dataclass

from ada.compositions.configuration_manager import (
    ConfigurationBackendSelection,
    EffectiveUserManagerPrincipalProvider,
    build_configuration_manager_surface,
    create_configuration_manager_dependencies,
    create_configuration_runtime_projection,
    create_manager_principal_binding_module,
    resolve_configuration_backend_selection,
)
from ada.compositions.manager_surface import (
    AdaManagerSurfaceComposition,
    create_ada_manager_surface_composition,
)
from ada.compositions.web_deployment import (
    AdaWebDeploymentDefinition,
    AdaWebDeploymentRuntime,
    open_ada_web_deployment_runtime,
)
from ada.configuration.tools import TOOL_COSMOS_REQUIREMENTS
from ada.configuration.tools.adapters import (
    CosmosToolProjectionRepository,
    CosmosToolProjectionSettings,
)
from atlanticus.web.application import create_web_application
from atlanticus.web.compositions.runtime_infrastructure import (
    SharePointInfrastructureSettings,
    resolve_sharepoint_infrastructure_settings,
)
from atlanticus.web.environment import EnvironmentReader, WebEnvironment, resolve_environment
from atlanticus.web.errors import WebConfigurationError
from atlanticus.web.manager import ManagerSurface
from atlanticus.web.models import WebApplicationRuntime
from integrated_operations.application.composition import (
    MANAGER_ROUTE_PREFIX,
    build_application_composition,
    build_web_definition,
)
from integrated_operations.deployment.definition import (
    build_deployment_definition,
    build_flask_config,
    build_metadata,
)
from integrated_operations.tool import resolve_projected_integrated_operations_manifest


@dataclass(slots=True)
class IntegratedOperationsApplicationRuntime:
    deployment: AdaWebDeploymentRuntime
    web: WebApplicationRuntime

    @property
    def server(self):
        return self.web.server

    def close(self) -> None:
        self.deployment.close()


def create_application_runtime() -> IntegratedOperationsApplicationRuntime:
    environment = EnvironmentReader()
    web_environment = resolve_environment()
    metadata = build_metadata()
    deployment_definition = build_deployment_definition(environment)
    backend_selection = _resolve_optional_configuration_backends(environment, web_environment)
    runtime_projection = _create_optional_runtime_projection(backend_selection, environment)
    sharepoint = _resolve_optional_sharepoint_settings(
        selection=backend_selection,
        environment=environment,
        definition=deployment_definition,
    )
    deployment = open_ada_web_deployment_runtime(
        definition=deployment_definition,
        metadata=metadata,
        environment=environment,
        runtime_projection=runtime_projection,
        sharepoint=sharepoint,
    )
    try:
        manager = _create_manager_composition(
            selection=backend_selection,
            environment=environment,
            web_environment=web_environment,
            deployment_definition=deployment_definition,
            deployment=deployment,
            sharepoint_ready=sharepoint is not None,
        )
        projection = _open_tool_projection(deployment)
        resolution = resolve_projected_integrated_operations_manifest(projection)
        composition = build_application_composition(
            tool_manifest_resolution=resolution,
            manager=manager,
        )
        web = create_web_application(
            build_web_definition(
                metadata=metadata,
                deployment_modules=deployment.bootstrap.modules,
                composition=composition,
                flask_config=build_flask_config(environment),
            )
        )
    except Exception:
        deployment.close()
        raise
    return IntegratedOperationsApplicationRuntime(
        deployment=deployment,
        web=web,
    )


def _resolve_optional_configuration_backends(
    environment: EnvironmentReader,
    web_environment: WebEnvironment,
) -> ConfigurationBackendSelection | None:
    try:
        return resolve_configuration_backend_selection(environment, web_environment)
    except WebConfigurationError, ValueError:
        return None


def _create_optional_runtime_projection(
    selection: ConfigurationBackendSelection | None,
    environment: EnvironmentReader,
):
    if selection is None:
        return None
    try:
        return create_configuration_runtime_projection(
            selection=selection,
            environment=environment,
        )
    except WebConfigurationError:
        return None


def _resolve_optional_sharepoint_settings(
    *,
    selection: ConfigurationBackendSelection | None,
    environment: EnvironmentReader,
    definition: AdaWebDeploymentDefinition,
) -> SharePointInfrastructureSettings | None:
    if selection is None or not selection.requires_sharepoint:
        return None
    try:
        return resolve_sharepoint_infrastructure_settings(environment, definition.sharepoint)
    except WebConfigurationError, ValueError:
        return None


def _create_manager_composition(
    *,
    selection: ConfigurationBackendSelection | None,
    environment: EnvironmentReader,
    web_environment: WebEnvironment,
    deployment_definition: AdaWebDeploymentDefinition,
    deployment: AdaWebDeploymentRuntime,
    sharepoint_ready: bool,
) -> AdaManagerSurfaceComposition | None:
    if selection is None:
        return None
    if selection.requires_sharepoint and not sharepoint_ready:
        return None

    principal_provider = EffectiveUserManagerPrincipalProvider()
    try:
        dependencies = create_configuration_manager_dependencies(
            selection=selection,
            infrastructure=deployment.infrastructure,
            sharepoint_infrastructure=(
                deployment.infrastructure if selection.requires_sharepoint else None
            ),
            bindings=deployment_definition.bindings,
            filenames=deployment_definition.configuration_filenames,
            principal_provider=principal_provider,
            environment=environment,
            web_environment=web_environment,
            force_publish_enabled=(web_environment.is_production and selection.requires_sharepoint),
        )
    except WebConfigurationError:
        return None

    surface = ManagerSurface(
        build_configuration_manager_surface(
            dependencies=dependencies,
            route_prefix=MANAGER_ROUTE_PREFIX,
        )
    )
    return create_ada_manager_surface_composition(
        surface=surface,
        principal_binding=create_manager_principal_binding_module(principal_provider),
    )


def _open_tool_projection(
    deployment: AdaWebDeploymentRuntime,
) -> CosmosToolProjectionRepository:
    requirements = TOOL_COSMOS_REQUIREMENTS
    if len(requirements) != 1:
        raise RuntimeError('Integrated Operations requires exactly one Tools Cosmos container')
    return CosmosToolProjectionRepository(
        client=deployment.bootstrap.infrastructure.cosmos(deployment.bootstrap.bindings.tools),
        settings=CosmosToolProjectionSettings(container_name=requirements[0].container_name),
    )
