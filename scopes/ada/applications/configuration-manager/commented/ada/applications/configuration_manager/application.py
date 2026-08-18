# Espejo pedagógico: conserva la misma lógica del archivo productivo.
# Los comentarios documentan la responsabilidad sin cambiar el comportamiento.
# Compone Manager, Tools, branding y Navigation sin poseer infraestructura.
from __future__ import annotations

from pathlib import Path

from dash import html

from ada.applications.configuration_manager.dependencies import (
    ConfigurationManagerDependencies,
)
from ada.applications.configuration_manager.workflows import ToolManagerWorkflowAdapter
from ada.configuration.tools.web import (
    ToolAdminWebContext,
    build_tool_admin_configuration,
    create_tool_admin_web_module,
)
from ada.ui.framework.core import create_ada_ui_module
from ada.ui.shell.navigation import (
    build_ada_navigation_desktop_trigger,
    build_ada_navigation_mobile_trigger,
    build_ada_navigation_offcanvas,
    create_ada_navigation_module,
)
from atlanticus.web.assets import AssetLayer
from atlanticus.web.manager import (
    ManagerApplicationDefinition,
    ManagerBrand,
    ManagerBrandMark,
    ManagerModule,
    ManagerModuleAccess,
    ManagerModuleGroup,
    ManagerPrincipal,
)
from atlanticus.web.manager.application import create_manager_application
from atlanticus.web.manager.web.ids import (
    workflow_action_id,
    workflow_draft_id,
    workflow_refresh_signal_id,
)
from atlanticus.web.models import ApplicationMetadata, DashSettings, WebApplicationRuntime
from atlanticus.web.modules import WebModule
from atlanticus.web.navigation import NavigationLink, NavigationMenu, NavigationUser
from atlanticus.web.services import ServiceRegistry

TOOLS_WORKFLOW_SERVICE = 'ada.configuration-manager.tools.workflow'
CONFIGURATION_MANAGER_ASSET_LAYER = AssetLayer(
    name='ada_configuration_manager',
    load_order=900,
    package='ada.applications.configuration_manager',
)
ATLANTICUS_CINZEL_STYLESHEET = (
    'https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&display=swap'
)


def create_configuration_manager_application(
    *,
    dependencies: ConfigurationManagerDependencies,
    publications_root: str | Path,
) -> WebApplicationRuntime:
    return create_manager_application(
        build_configuration_manager_definition(
            dependencies=dependencies,
            publications_root=publications_root,
        )
    )


def build_configuration_manager_definition(
    *,
    dependencies: ConfigurationManagerDependencies,
    publications_root: str | Path,
) -> ManagerApplicationDefinition:
    tool_context = ToolAdminWebContext(
        services=dependencies.tools,
        draft_store_id=workflow_draft_id('tools'),
        draft_save_action_id=workflow_action_id('tools', 'save-draft'),
        workflow_refresh_signal_id=workflow_refresh_signal_id('tools'),
        draft_owner_provider=lambda: dependencies.principal_provider().subject_id,
        can_manage=lambda: _can_manage_tools(dependencies.principal_provider()),
        source_name=dependencies.tools_source_name,
        projection_name=dependencies.tools_projection_name,
    )
    return ManagerApplicationDefinition(
        import_name='ada.applications.configuration_manager',
        metadata=ApplicationMetadata(
            application_id='ada-configuration-manager',
            display_name='Gestor de configuración ADA',
            version='0.1.0',
        ),
        publications_root=Path(publications_root),
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
            ),
        ),
        subtitle=(
            'Asistente de decisiones ágiles · '
            'Configuraciones revisionadas y proyecciones de consumo'
        ),
        current_path='/tools',
        brand=_build_brand(),
        web_modules=(
            WebModule(
                name='ada-configuration-manager-services',
                asset_layers=(CONFIGURATION_MANAGER_ASSET_LAYER,),
                register_services=lambda services: _register_services(services, dependencies),
            ),
            create_ada_ui_module(),
            create_ada_navigation_module(),
        ),
        header_actions=lambda _services: _build_navigation_triggers(),
        shell_overlays=lambda _services: build_ada_navigation_offcanvas(
            _build_navigation_menu(dependencies.principal_provider())
        ),
        dash=DashSettings(
            external_stylesheets=(ATLANTICUS_CINZEL_STYLESHEET,),
            update_title=None,
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


def _build_brand() -> ManagerBrand:
    root = f'/assets/{CONFIGURATION_MANAGER_ASSET_LAYER.target_name}/img'
    return ManagerBrand(
        marks=(
            ManagerBrandMark(
                role='product',
                logo_src=f'{root}/ada-primary.svg',
                logo_alt='ADA',
            ),
            ManagerBrandMark(
                role='framework',
                logo_src=f'{root}/atlanticus-primary.png',
                logo_alt='Atlanticus',
                label='ATLANTICUS',
                eyebrow='Framework',
            ),
            ManagerBrandMark(
                role='organization',
                logo_src=f'{root}/mlp-primary.svg',
                logo_alt='Minera Los Pelambres',
                label='Minera Los Pelambres',
            ),
        )
    )


def _build_navigation_triggers() -> object:
    return html.Div(
        [
            build_ada_navigation_desktop_trigger(),
            build_ada_navigation_mobile_trigger(),
        ],
        className='atlanticus-manager__navigation-triggers',
    )


def _build_navigation_menu(principal: ManagerPrincipal) -> NavigationMenu:
    return NavigationMenu(
        user=NavigationUser(
            display_name=principal.display_name,
            profile_key='administrator',
            profile_label='Administrador',
            profile_color='#C9A24B',
            avatar_text=_avatar_text(principal.display_name),
        ),
        links=(
            NavigationLink(
                key='configuration-manager',
                label='Gestor de configuración',
                href='/tools',
                order=10,
                icon='bi bi-sliders',
            ),
        ),
    )


def _avatar_text(display_name: str) -> str:
    words = [word for word in display_name.split() if word]
    if not words:
        return 'A'
    return ''.join(word[0].upper() for word in words[:2])


def _can_manage_tools(principal: ManagerPrincipal) -> bool:
    return (
        principal.is_local
        or 'administrator' in principal.profile_keys
        or 'tools.manage' in principal.access_keys
    )
