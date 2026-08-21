from __future__ import annotations

# Espejo comentado: misma lógica productiva con notas pedagógicas en español.

from dataclasses import dataclass
from pathlib import Path

from dash import Input, Output, dcc, html, page_container

from ada.compositions.configuration_manager import (
    EffectiveUserManagerPrincipalProvider,
    build_configuration_manager_surface,
    create_configuration_manager_dependencies,
    create_configuration_runtime_projection,
    create_manager_principal_binding_module,
    open_configuration_manager_sharepoint_infrastructure,
    resolve_configuration_backend_selection,
)
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
from atlanticus.web.compositions.runtime_infrastructure import WebRuntimeInfrastructure
from atlanticus.web.environment import EnvironmentReader, resolve_environment
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.manager import ManagerSurface
from atlanticus.web.models import WebApplicationDefinition, WebApplicationRuntime
from atlanticus.web.modules import WebModule

_LOCATION_ID = 'ada-application-base-location'
_PAGE_HOST_ID = 'ada-application-base-page-host'
_MANAGER_HOST_ID = 'ada-application-base-manager-host'
_MANAGER_ROUTE_PREFIX = '/manager'


@dataclass(slots=True)
class AdaApplicationBaseRuntime:
    deployment: AdaWebDeploymentRuntime
    web: WebApplicationRuntime
    manager_sharepoint_infrastructure: WebRuntimeInfrastructure | None = None

    @property
    def server(self):
        return self.web.server

    def close(self) -> None:
        manager_error = None
        try:
            if self.manager_sharepoint_infrastructure is not None:
                self.manager_sharepoint_infrastructure.close()
        except Exception as error:
            manager_error = error
        try:
            self.deployment.close()
        except Exception:
            if manager_error is None:
                raise
        if manager_error is not None:
            raise manager_error


# La aplicación resuelve una sola vez la proyección seleccionada y la comparte con el bootstrap.
def create_application_runtime() -> AdaApplicationBaseRuntime:
    environment = EnvironmentReader()
    web_environment = resolve_environment()
    metadata = build_metadata()
    deployment_definition = build_deployment_definition(environment)
    backend_selection = resolve_configuration_backend_selection(
        environment,
        web_environment,
    )
    runtime_projection = create_configuration_runtime_projection(
        selection=backend_selection,
        environment=environment,
    )
    deployment = open_ada_web_deployment_runtime(
        definition=deployment_definition,
        metadata=metadata,
        environment=environment,
        runtime_projection=runtime_projection,
    )
    manager_sharepoint_infrastructure = None
    try:
        manager_sharepoint_infrastructure = (
            open_configuration_manager_sharepoint_infrastructure(
                selection=backend_selection,
                environment=environment,
                definition=deployment_definition.sharepoint,
            )
        )
        principal_provider = EffectiveUserManagerPrincipalProvider()
        manager_dependencies = create_configuration_manager_dependencies(
            selection=backend_selection,
            infrastructure=deployment.infrastructure,
            sharepoint_infrastructure=manager_sharepoint_infrastructure,
            bindings=deployment_definition.bindings,
            filenames=deployment_definition.configuration_filenames,
            principal_provider=principal_provider,
            environment=environment,
        )
        manager_surface = ManagerSurface(
            build_configuration_manager_surface(
                dependencies=manager_dependencies,
                route_prefix=_MANAGER_ROUTE_PREFIX,
            )
        )
        modules = (
            *deployment.bootstrap.modules,
            create_manager_principal_binding_module(principal_provider),
            *manager_surface.web_modules,
            _create_manager_host_module(),
        )
        web = create_web_application(
            WebApplicationDefinition(
                import_name='ada_application_base',
                metadata=metadata,
                publications_root=Path.cwd() / '.runtime' / 'assets',
                layout=lambda services: _build_layout(services, manager_surface),
                modules=modules,
                page_packages=('ada_application_base.pages',),
                index=IndexPageDefinition(language='es'),
                flask_config=build_flask_config(environment),
            )
        )
    except Exception:
        if manager_sharepoint_infrastructure is not None:
            _close_quietly(manager_sharepoint_infrastructure)
        deployment.close()
        raise
    return AdaApplicationBaseRuntime(
        deployment=deployment,
        web=web,
        manager_sharepoint_infrastructure=manager_sharepoint_infrastructure,
    )


def _build_layout(services, manager_surface: ManagerSurface) -> object:
    return html.Div(
        [
            dcc.Location(id=_LOCATION_ID, refresh=False),
            html.Div(page_container, id=_PAGE_HOST_ID),
            html.Div(
                manager_surface.layout(services),
                id=_MANAGER_HOST_ID,
                hidden=True,
            ),
        ]
    )


def _create_manager_host_module() -> WebModule:
    def register_callbacks(app: object, _services: object) -> None:
        @app.callback(
            Output(_PAGE_HOST_ID, 'hidden'),
            Output(_MANAGER_HOST_ID, 'hidden'),
            Input(_LOCATION_ID, 'pathname'),
        )
        def select_surface(pathname: str | None):
            manager_route = _is_manager_route(pathname)
            return manager_route, not manager_route

    return WebModule(
        name='ada-application-base-manager-host',
        register_callbacks=register_callbacks,
    )


def _is_manager_route(pathname: str | None) -> bool:
    if not pathname:
        return False
    return pathname == _MANAGER_ROUTE_PREFIX or pathname.startswith(
        f'{_MANAGER_ROUTE_PREFIX}/'
    )


def _close_quietly(infrastructure: WebRuntimeInfrastructure) -> None:
    try:
        infrastructure.close()
    except Exception:
        return
