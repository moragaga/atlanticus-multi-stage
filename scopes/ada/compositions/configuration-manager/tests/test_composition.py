from ada.compositions.configuration_manager import (
    NAVIGATION_WORKFLOW_SERVICE,
    TOOLS_WORKFLOW_SERVICE,
    USERS_WORKFLOW_SERVICE,
    ConfigurationManagerDependencies,
    build_configuration_manager_surface,
)
from atlanticus.web.manager import ManagerModuleRegistry, ManagerPrincipal


def _dependencies() -> ConfigurationManagerDependencies:
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
