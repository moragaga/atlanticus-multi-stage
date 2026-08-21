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

from atlanticus.web.application import create_web_application
from atlanticus.web.environment import EnvironmentReader
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.models import WebApplicationDefinition, WebApplicationRuntime


@dataclass(slots=True)
class AdaApplicationBaseRuntime:
    # El artifact posee el deployment runtime y la aplicación Web que éste alimenta.
    deployment: AdaWebDeploymentRuntime
    web: WebApplicationRuntime

    @property
    def server(self):
        # Expone Flask sin duplicar el runtime Web.
        return self.web.server

    def close(self) -> None:
        # El cierre del deployment libera la infraestructura Cosmos del proceso.
        self.deployment.close()


def create_application_runtime() -> AdaApplicationBaseRuntime:
    # Toma un snapshot único del entorno para resolver de forma coherente este runtime.
    environment = EnvironmentReader()
    metadata = build_metadata()
    # Esta fase sólo abre runtime; deployment resuelve Identity/Users desde ATLANTICUS_ENVIRONMENT.
    deployment = open_ada_web_deployment_runtime(
        definition=build_deployment_definition(environment),
        metadata=metadata,
        environment=environment,
    )
    try:
        # Reutiliza directamente los módulos certificados por R17B: Identity, Users,
        # Navigation/Authorization y Activity.
        web = create_web_application(
            WebApplicationDefinition(
                import_name='ada_application_base',
                metadata=metadata,
                publications_root=Path.cwd() / '.runtime' / 'assets',
                layout=lambda _services: page_container,
                modules=deployment.bootstrap.modules,
                page_packages=('ada_application_base.pages',),
                index=IndexPageDefinition(language='es'),
                # El artifact sólo traduce el secreto entregado por deployment a Flask.
                flask_config=build_flask_config(environment),
            )
        )
    except Exception:
        # Si falla la composición Web no se deja infraestructura abierta.
        deployment.close()
        raise
    return AdaApplicationBaseRuntime(deployment=deployment, web=web)
