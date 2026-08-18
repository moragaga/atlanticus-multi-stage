# Espejo pedagógico: este archivo conserva exactamente la lógica del código productivo.
# Capability genérica del Configuration Manager de Atlanticus. Mantiene contratos y UI administrativa sin conocer dominios ni persistencias concretas.
# Los comentarios explican la intención arquitectónica; no agregan ramas, estado ni comportamiento.

from atlanticus.web.application import create_web_application
from atlanticus.web.manager.authorization import (
    DefaultManagerAuthorizationPolicy,
    ManagerAuthorizationPolicy,
)
from atlanticus.web.manager.errors import ManagerDefinitionError
from atlanticus.web.manager.models import ManagerApplicationDefinition
from atlanticus.web.manager.registry import ManagerModuleRegistry
from atlanticus.web.manager.web import (
    build_manager_shell,
    manager_asset_layer,
    register_manager_callbacks,
)
from atlanticus.web.models import WebApplicationDefinition, WebApplicationRuntime
from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry


def build_manager_web_definition(
    definition: ManagerApplicationDefinition,
    *,
    authorization: ManagerAuthorizationPolicy | None = None,
) -> WebApplicationDefinition:
    if not definition.subtitle.strip():
        raise ManagerDefinitionError('Manager application subtitle must not be empty')
    if not definition.current_path.startswith('/'):
        raise ManagerDefinitionError('Manager application path must start with slash')
    registry = ManagerModuleRegistry(definition.groups, definition.modules)
    policy = authorization or DefaultManagerAuthorizationPolicy()

    def register_callbacks(app: object, services: ServiceRegistry) -> None:
        register_manager_callbacks(
            app,
            definition=definition,
            registry=registry,
            services=services,
            authorization=policy,
        )

    manager_module = WebModule(
        name='manager',
        page_packages=('atlanticus.web.manager.pages',),
        asset_layers=(manager_asset_layer(),),
        register_callbacks=register_callbacks,
    )
    module_web_modules = tuple(
        module.web_module for module in registry.modules if module.web_module is not None
    )
    return WebApplicationDefinition(
        import_name=definition.import_name,
        metadata=definition.metadata,
        publications_root=definition.publications_root,
        layout=lambda services: build_manager_shell(
            definition=definition,
            registry=registry,
            services=services,
            principal=definition.principal_provider(),
            authorization=policy,
        ),
        modules=definition.web_modules + module_web_modules + (manager_module,),
        index=definition.index,
        dash=definition.dash,
        flask_config=definition.flask_config,
    )


def create_manager_application(
    definition: ManagerApplicationDefinition,
    *,
    authorization: ManagerAuthorizationPolicy | None = None,
) -> WebApplicationRuntime:
    return create_web_application(
        build_manager_web_definition(definition, authorization=authorization)
    )
