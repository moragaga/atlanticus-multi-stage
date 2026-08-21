from __future__ import annotations

from pathlib import Path

from dash import html

from ada.compositions.configuration_manager import (
    ConfigurationManagerDependencies,
    build_configuration_manager_surface,
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
    ManagerPrincipal,
)
from atlanticus.web.manager.application import create_manager_application
from atlanticus.web.models import ApplicationMetadata, DashSettings, WebApplicationRuntime
from atlanticus.web.modules import WebModule
from atlanticus.web.navigation.api import NavigationLink, NavigationMenu, NavigationUser

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
    return ManagerApplicationDefinition(
        import_name='ada.applications.configuration_manager',
        metadata=ApplicationMetadata(
            application_id='ada-configuration-manager',
            display_name='Gestor de configuración ADA',
            version='0.2.3',
        ),
        publications_root=Path(publications_root),
        surface=build_configuration_manager_surface(
            dependencies=dependencies,
            route_prefix='',
        ),
        subtitle=(
            'Asistente de decisiones ágiles · '
            'Configuraciones revisionadas y proyecciones de consumo'
        ),
        brand=_build_brand(),
        web_modules=(
            WebModule(
                name='ada-configuration-manager-assets',
                asset_layers=(CONFIGURATION_MANAGER_ASSET_LAYER,),
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
            profile_background_color='#C9A24B',
            profile_text_color='#071522',
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
