# El runtime abre la proyección Tools desde la conexión Cosmos nombrada por el bootstrap.
# La autoridad estructural de Operaciones Integradas proviene de esa proyección y no de una constante del artifact.
from __future__ import annotations

from dataclasses import dataclass

from ada.compositions.web_deployment import (
    AdaWebDeploymentRuntime,
    open_ada_web_deployment_runtime,
)
from ada.configuration.tools import TOOL_COSMOS_REQUIREMENTS
from ada.configuration.tools.adapters import (
    CosmosToolProjectionRepository,
    CosmosToolProjectionSettings,
)
from atlanticus.web.application import create_web_application
from atlanticus.web.environment import EnvironmentReader
from atlanticus.web.models import WebApplicationRuntime
from integrated_operations.application.composition import build_web_definition
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
    metadata = build_metadata()
    deployment = open_ada_web_deployment_runtime(
        definition=build_deployment_definition(environment),
        metadata=metadata,
        environment=environment,
    )
    try:
        projection = _open_tool_projection(deployment)
        resolution = resolve_projected_integrated_operations_manifest(projection)
        web = create_web_application(
            build_web_definition(
                metadata=metadata,
                deployment_modules=deployment.bootstrap.modules,
                tool_manifest_resolution=resolution,
                flask_config=build_flask_config(environment),
            )
        )
    except Exception:
        deployment.close()
        raise
    return IntegratedOperationsApplicationRuntime(deployment=deployment, web=web)


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
