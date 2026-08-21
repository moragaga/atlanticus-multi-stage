from __future__ import annotations

from dataclasses import dataclass

from ada.compositions.web_deployment import (
    AdaWebDeploymentRuntime,
    open_ada_web_deployment_runtime,
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
        web = create_web_application(
            build_web_definition(
                metadata=metadata,
                deployment_modules=deployment.bootstrap.modules,
                flask_config=build_flask_config(environment),
            )
        )
    except Exception:
        deployment.close()
        raise
    return IntegratedOperationsApplicationRuntime(deployment=deployment, web=web)
