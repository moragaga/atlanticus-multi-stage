from ada.compositions.configuration_manager.dependencies import (
    ConfigurationManagerDependencies,
)
from ada.compositions.configuration_manager.workflows import (
    NavigationManagerWorkflowAdapter,
    ToolManagerWorkflowAdapter,
    UsersManagerWorkflowAdapter,
)
from ada.configuration.tools.web import (
    ToolAdminWebContext,
    build_tool_admin_configuration,
    build_tool_history_preview,
    create_tool_admin_web_module,
)
from atlanticus.web.manager import (
    ManagerModule,
    ManagerModuleAccess,
    ManagerModuleGroup,
    ManagerPrincipal,
    ManagerSurfaceDefinition,
)
from atlanticus.web.manager.web.ids import (
    workflow_action_id,
    workflow_draft_id,
    workflow_editor_revision_id,
    workflow_refresh_signal_id,
)
from atlanticus.web.modules import WebModule
from atlanticus.web.navigation.configuration import NavigationProfileOption
from atlanticus.web.navigation.configuration.web import (
    NavigationAdminWebContext,
    build_navigation_admin_configuration,
    build_navigation_history_preview,
    create_navigation_admin_web_module,
)
from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.configuration.web import (
    UsersAdminWebContext,
    build_users_admin_configuration,
    build_users_history_preview,
    create_users_admin_web_module,
)

TOOLS_WORKFLOW_SERVICE = 'ada.configuration-manager.tools.workflow'
USERS_WORKFLOW_SERVICE = 'ada.configuration-manager.users.workflow'
NAVIGATION_WORKFLOW_SERVICE = 'ada.configuration-manager.navigation.workflow'


def build_configuration_manager_surface(
    *,
    dependencies: ConfigurationManagerDependencies,
    route_prefix: str = '/manager',
) -> ManagerSurfaceDefinition:
    tool_context = ToolAdminWebContext(
        services=dependencies.tools,
        draft_store_id=workflow_draft_id('tools'),
        draft_save_action_id=workflow_action_id('tools', 'save-draft'),
        workflow_refresh_signal_id=workflow_refresh_signal_id('tools'),
        editor_revision_store_id=workflow_editor_revision_id('tools'),
        draft_owner_provider=lambda: dependencies.principal_provider().subject_id,
        can_manage=lambda: _can_manage_tools(dependencies.principal_provider()),
        source_name=dependencies.tools_source_name,
        projection_name=dependencies.tools_projection_name,
    )
    users_context = UsersAdminWebContext(
        services=dependencies.users,
        draft_store_id=workflow_draft_id('users'),
        draft_save_action_id=workflow_action_id('users', 'save-draft'),
        workflow_refresh_signal_id=workflow_refresh_signal_id('users'),
        editor_revision_store_id=workflow_editor_revision_id('users'),
        draft_owner_provider=lambda: dependencies.principal_provider().subject_id,
        can_manage=lambda: _can_manage_users(dependencies.principal_provider()),
        source_name=dependencies.users_source_name,
        projection_name=dependencies.users_projection_name,
    )
    navigation_context = NavigationAdminWebContext(
        services=dependencies.navigation,
        draft_store_id=workflow_draft_id('navigation'),
        draft_save_action_id=workflow_action_id('navigation', 'save-draft'),
        workflow_refresh_signal_id=workflow_refresh_signal_id('navigation'),
        editor_revision_store_id=workflow_editor_revision_id('navigation'),
        draft_owner_provider=lambda: dependencies.principal_provider().subject_id,
        can_manage=lambda: _can_manage_navigation(dependencies.principal_provider()),
        source_name=dependencies.navigation_source_name,
        projection_name=dependencies.navigation_projection_name,
        profile_options_provider=lambda: _navigation_profile_options(dependencies),
    )
    return ManagerSurfaceDefinition(
        principal_provider=dependencies.principal_provider,
        groups=(
            ManagerModuleGroup(
                key='configuration',
                title='Configuraciones',
                order=10,
            ),
        ),
        modules=(
            ManagerModule(
                key='tools',
                group_key='configuration',
                title='Herramientas',
                route='/tools',
                order=10,
                description='Estructura base de las herramientas ADA.',
                layout=lambda _services: build_tool_admin_configuration(tool_context),
                history_preview_renderer=build_tool_history_preview,
                workflow_service=TOOLS_WORKFLOW_SERVICE,
                access=ManagerModuleAccess(
                    view='tools.manage',
                    validate='tools.manage',
                    project='tools.manage',
                    publish='tools.manage',
                ),
                web_module=create_tool_admin_web_module(tool_context),
                workflow_section_title='Estado y trazabilidad',
                content_section_title='Configuración de herramienta',
                source_name=dependencies.tools_source_name,
                projection_name=dependencies.tools_projection_name,
                force_publish_enabled=dependencies.force_publish_enabled,
            ),
            ManagerModule(
                key='users',
                group_key='configuration',
                title='Usuarios',
                route='/users',
                order=20,
                description='Perfiles, usuarios y descubrimiento de identidades Atlanticus.',
                layout=lambda _services: build_users_admin_configuration(users_context),
                history_preview_renderer=build_users_history_preview,
                workflow_service=USERS_WORKFLOW_SERVICE,
                access=ManagerModuleAccess(
                    view='users.manage',
                    validate='users.manage',
                    project='users.manage',
                    publish='users.manage',
                ),
                web_module=create_users_admin_web_module(users_context),
                workflow_section_title='Estado y trazabilidad',
                content_section_title='Usuarios y perfiles',
                source_name=dependencies.users_source_name,
                projection_name=dependencies.users_projection_name,
                force_publish_enabled=dependencies.force_publish_enabled,
            ),
            ManagerModule(
                key='navigation',
                group_key='configuration',
                title='Navegación',
                route='/navigation',
                order=30,
                description='Rutas, secciones y políticas de acceso de Navigation.',
                layout=lambda _services: build_navigation_admin_configuration(navigation_context),
                history_preview_renderer=build_navigation_history_preview,
                workflow_service=NAVIGATION_WORKFLOW_SERVICE,
                access=ManagerModuleAccess(
                    view='navigation.manage',
                    validate='navigation.manage',
                    project='navigation.manage',
                    publish='navigation.manage',
                ),
                web_module=create_navigation_admin_web_module(navigation_context),
                workflow_section_title='Estado y trazabilidad',
                content_section_title='Navegación',
                source_name=dependencies.navigation_source_name,
                projection_name=dependencies.navigation_projection_name,
                force_publish_enabled=dependencies.force_publish_enabled,
            ),
        ),
        default_module_key='tools',
        route_prefix=route_prefix,
        web_modules=(
            WebModule(
                name='ada-configuration-manager-services',
                register_services=lambda services: _register_services(services, dependencies),
            ),
        ),
    )


def _register_services(
    services: ServiceRegistry,
    dependencies: ConfigurationManagerDependencies,
) -> None:
    services.add(
        TOOLS_WORKFLOW_SERVICE,
        ToolManagerWorkflowAdapter(dependencies.tools),
    )
    services.add(
        USERS_WORKFLOW_SERVICE,
        UsersManagerWorkflowAdapter(dependencies.users),
    )
    services.add(
        NAVIGATION_WORKFLOW_SERVICE,
        NavigationManagerWorkflowAdapter(dependencies.navigation),
    )


def _can_manage_tools(principal: ManagerPrincipal) -> bool:
    return (
        principal.is_local
        or 'administrator' in principal.profile_keys
        or 'tools.manage' in principal.access_keys
    )


def _can_manage_users(principal: ManagerPrincipal) -> bool:
    return (
        principal.is_local
        or 'administrator' in principal.profile_keys
        or 'users.manage' in principal.access_keys
    )


def _can_manage_navigation(principal: ManagerPrincipal) -> bool:
    return (
        principal.is_local
        or 'administrator' in principal.profile_keys
        or 'navigation.manage' in principal.access_keys
    )


def _navigation_profile_options(
    dependencies: ConfigurationManagerDependencies,
) -> tuple[NavigationProfileOption, ...]:
    try:
        users_catalog = dependencies.users.administration.load_catalog()
        profile_catalog = users_catalog.profile_catalog() if users_catalog is not None else None
    except Exception:
        profile_catalog = None
    if profile_catalog is None:
        return ()
    return tuple(
        NavigationProfileOption(
            key=profile.key,
            label=profile.label,
            unrestricted=profile.key in {'local', 'administrator'},
            background_color=profile.background_color,
            text_color=profile.text_color,
        )
        for profile in profile_catalog.all()
    )
