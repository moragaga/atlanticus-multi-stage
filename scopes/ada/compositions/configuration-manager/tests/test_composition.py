from types import SimpleNamespace

from ada.compositions.configuration_manager import (
    NAVIGATION_WORKFLOW_SERVICE,
    NAVIGATION_WORKSPACE_IMPORT_SERVICE,
    TOOLS_WORKFLOW_SERVICE,
    TOOLS_WORKSPACE_IMPORT_SERVICE,
    USERS_WORKFLOW_SERVICE,
    USERS_WORKSPACE_IMPORT_SERVICE,
    ConfigurationManagerDependencies,
    build_configuration_manager_surface,
)
from atlanticus.web.manager import ManagerModuleRegistry, ManagerPrincipal
from atlanticus.web.services import ServiceRegistry


def _dependencies(
    *,
    force_publish_enabled: bool = False,
    workspace_import: bool = False,
) -> ConfigurationManagerDependencies:
    return ConfigurationManagerDependencies(
        tools=object(),
        users=object(),
        navigation=object(),
        principal_provider=lambda: ManagerPrincipal(
            subject_id='local',
            display_name='Administrador local',
            is_local=True,
        ),
        tools_source_name='Archivo local',
        tools_projection_name='Archivo local',
        users_source_name='Archivo local',
        users_projection_name='Archivo local',
        navigation_source_name='Archivo local',
        navigation_projection_name='Archivo local',
        tools_workspace_import=object() if workspace_import else None,
        users_workspace_import=object() if workspace_import else None,
        navigation_workspace_import=object() if workspace_import else None,
        tools_workspace_import_name='Archivo local' if workspace_import else None,
        users_workspace_import_name='Archivo local' if workspace_import else None,
        navigation_workspace_import_name='Archivo local' if workspace_import else None,
        force_publish_enabled=force_publish_enabled,
    )


def test_configuration_manager_surface_registers_existing_modules_under_manager() -> None:
    surface = build_configuration_manager_surface(dependencies=_dependencies())
    registry = ManagerModuleRegistry(
        surface.groups,
        surface.modules,
        route_prefix=surface.route_prefix,
    )
    tools, users, navigation = surface.modules

    assert surface.default_module_key == 'tools'
    assert surface.route_prefix == '/manager'
    assert [module.key for module in surface.modules] == ['tools', 'users', 'navigation']
    assert tools.route == '/tools'
    assert users.route == '/users'
    assert navigation.route == '/navigation'
    assert registry.route_for(tools) == '/manager/tools'
    assert registry.route_for(users) == '/manager/users'
    assert registry.route_for(navigation) == '/manager/navigation'
    assert tools.workflow_service == TOOLS_WORKFLOW_SERVICE
    assert users.workflow_service == USERS_WORKFLOW_SERVICE
    assert navigation.workflow_service == NAVIGATION_WORKFLOW_SERVICE


def test_configuration_manager_surface_owns_services_not_standalone_host() -> None:
    surface = build_configuration_manager_surface(dependencies=_dependencies())

    assert [module.name for module in surface.web_modules] == ['ada-configuration-manager-services']
    assert surface.web_modules[0].register_services is not None


def test_force_publication_capability_is_explicitly_propagated_to_all_modules() -> None:
    surface = build_configuration_manager_surface(
        dependencies=_dependencies(force_publish_enabled=True)
    )

    assert all(module.force_publish_enabled for module in surface.modules)


def test_configuration_manager_surface_registers_semantic_history_previews() -> None:
    surface = build_configuration_manager_surface(dependencies=_dependencies())

    renderers = {module.key: module.history_preview_renderer for module in surface.modules}

    assert renderers['tools'] is not None
    assert renderers['users'] is not None
    assert renderers['navigation'] is not None
    assert renderers['tools'].__name__ == 'build_tool_history_preview'
    assert renderers['users'].__name__ == 'build_users_history_preview'
    assert renderers['navigation'].__name__ == 'build_navigation_history_preview'


def test_configuration_manager_surface_propagates_optional_workspace_imports() -> None:
    surface = build_configuration_manager_surface(dependencies=_dependencies(workspace_import=True))
    ManagerModuleRegistry(
        surface.groups,
        surface.modules,
        route_prefix=surface.route_prefix,
    )
    tools, users, navigation = surface.modules

    assert tools.workspace_import_service == TOOLS_WORKSPACE_IMPORT_SERVICE
    assert users.workspace_import_service == USERS_WORKSPACE_IMPORT_SERVICE
    assert navigation.workspace_import_service == NAVIGATION_WORKSPACE_IMPORT_SERVICE
    assert tools.workspace_import_name == 'Archivo local'
    assert users.workspace_import_name == 'Archivo local'
    assert navigation.workspace_import_name == 'Archivo local'


def test_configuration_manager_surface_omits_workspace_imports_when_not_configured() -> None:
    surface = build_configuration_manager_surface(dependencies=_dependencies())

    assert all(module.workspace_import_service is None for module in surface.modules)
    assert all(module.workspace_import_name is None for module in surface.modules)


def test_configuration_manager_registers_workspace_import_services_separately() -> None:
    service = SimpleNamespace(projection_workflow=object(), administration=object())
    tools_import = object()
    users_import = object()
    navigation_import = object()
    dependencies = ConfigurationManagerDependencies(
        tools=service,
        users=service,
        navigation=service,
        principal_provider=lambda: ManagerPrincipal(
            subject_id='principal-current',
            display_name='Current Principal',
        ),
        tools_workspace_import=tools_import,
        users_workspace_import=users_import,
        navigation_workspace_import=navigation_import,
        tools_workspace_import_name='Archivo local',
        users_workspace_import_name='Archivo local',
        navigation_workspace_import_name='Archivo local',
    )
    surface = build_configuration_manager_surface(dependencies=dependencies)
    services = ServiceRegistry()

    surface.web_modules[0].register_services(services)

    assert services.require(TOOLS_WORKSPACE_IMPORT_SERVICE) is tools_import
    assert services.require(USERS_WORKSPACE_IMPORT_SERVICE) is users_import
    assert services.require(NAVIGATION_WORKSPACE_IMPORT_SERVICE) is navigation_import
    assert services.contains(TOOLS_WORKFLOW_SERVICE)
    assert services.contains(USERS_WORKFLOW_SERVICE)
    assert services.contains(NAVIGATION_WORKFLOW_SERVICE)
