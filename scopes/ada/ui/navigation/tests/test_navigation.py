from pathlib import Path

import dash_bootstrap_components as dbc

from ada.ui.navigation import (
    ADA_NAVIGATION_ASSET_LAYER,
    build_ada_navigation_desktop_trigger,
    build_ada_navigation_offcanvas,
    create_ada_navigation_module,
)
from atlanticus.web.navigation import (
    NavigationGroup,
    NavigationLink,
    NavigationMenu,
    NavigationUser,
)


def _menu() -> NavigationMenu:
    return NavigationMenu(
        user=NavigationUser(
            display_name='Usuario ADA',
            email='usuario@local.ada',
            profile='Administrador',
            initials='UA',
        ),
        links=(
            NavigationLink(
                key='home',
                label='Inicio',
                href='/',
                order=0,
                icon='bi bi-house',
            ),
        ),
        groups=(
            NavigationGroup(
                key='configuration',
                label='CONFIGURACIÓN',
                order=10,
                icon='bi bi-gear',
                links=(
                    NavigationLink(
                        key='status',
                        label='Status',
                        href='/status',
                        icon='bi bi-card-list',
                    ),
                ),
            ),
        ),
    )


def test_ada_navigation_is_only_a_presentation_module() -> None:
    module = create_ada_navigation_module()

    assert module.name == 'ada-navigation'
    assert module.asset_layers == (ADA_NAVIGATION_ASSET_LAYER,)
    assert ADA_NAVIGATION_ASSET_LAYER.load_order == 200
    assert module.register_services is None
    assert module.register_callbacks is not None


def test_approved_desktop_trigger_contract_is_preserved() -> None:
    trigger = build_ada_navigation_desktop_trigger()
    props = trigger.to_plotly_json()['props']

    assert isinstance(trigger, dbc.Button)
    assert props['id'] == 'app-header-desktop-toggle'
    assert props['className'] == 'dashboard-menu-btn-desktop d-none d-md-flex dark-theme'
    assert props['color'] == 'dark'
    assert props['n_clicks'] == 0


def test_approved_offcanvas_contract_is_preserved() -> None:
    component = build_ada_navigation_offcanvas(_menu())
    props = component.to_plotly_json()['props']

    assert isinstance(component, dbc.Offcanvas)
    assert props['id'] == 'app-header-offcanvas'
    assert props['className'] == 'dashboard-main-offcanvas app-navigation-offcanvas'
    assert props['placement'] == 'end'
    assert props['is_open'] is False


def test_approved_navigation_css_is_copied_without_redesign() -> None:
    css = (
        Path(__file__).parents[1]
        / 'src'
        / 'ada'
        / 'ui'
        / 'navigation'
        / 'resources'
        / 'css'
        / '10_navigation.css'
    ).read_text(encoding='utf-8')

    assert '.dashboard-menu-btn-desktop {' in css
    assert 'right: -10px;' in css
    assert 'width 0.18s ease' in css
    assert '.dashboard-menu-btn-desktop:hover {' in css
    assert 'right: -12px;' in css
    assert '.app-navigation-offcanvas' in css
