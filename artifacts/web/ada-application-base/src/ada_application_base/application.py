from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dash import page_container

from ada.compositions.web_deployment import (
    AdaWebDeploymentRuntime,
    open_ada_web_deployment_runtime,
)
from ada_application_base.definition import (
    build_deployment_definition,
    build_flask_config,
    build_metadata,
)
from ada_application_base.identity import build_identity_provider
from atlanticus.web.application import create_web_application
from atlanticus.web.environment import EnvironmentReader
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.models import WebApplicationDefinition, WebApplicationRuntime


@dataclass(slots=True)
class AdaApplicationBaseRuntime:
    deployment: AdaWebDeploymentRuntime
    web: WebApplicationRuntime

    @property
    def server(self):
        return self.web.server

    def close(self) -> None:
        self.deployment.close()


def create_application_runtime() -> AdaApplicationBaseRuntime:
    environment = EnvironmentReader()
    metadata = build_metadata()
    deployment = open_ada_web_deployment_runtime(
        definition=build_deployment_definition(environment),
        metadata=metadata,
        identity_provider=build_identity_provider(),
        environment=environment,
    )
    try:
        web = create_web_application(
            WebApplicationDefinition(
                import_name='ada_application_base',
                metadata=metadata,
                publications_root=Path.cwd() / '.runtime' / 'assets',
                layout=lambda _services: page_container,
                modules=deployment.bootstrap.modules,
                page_packages=('ada_application_base.pages',),
                index=IndexPageDefinition(language='es'),
                flask_config=build_flask_config(environment),
            )
        )
    except Exception:
        deployment.close()
        raise
    return AdaApplicationBaseRuntime(deployment=deployment, web=web)
