from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from ada.ui.shell.navigation.constants import (
    ADA_NAVIGATION_SUBTITLE,
    ADA_NAVIGATION_TITLE,
    ADA_PROJECTS_LABEL,
    ADA_PROJECTS_URL,
)
from ada.ui.shell.navigation.ids import AdaNavigationIds
from atlanticus.web.navigation import (
    NavigationGroup,
    NavigationLink,
    NavigationMenu,
    NavigationUser,
    resolve_navigation_from_services,
)
from atlanticus.web.services import ServiceRegistry


def build_ada_navigation_desktop_trigger() -> dbc.Button:
    return dbc.Button(
        id=AdaNavigationIds.HEADER_DESKTOP_TOGGLE,
        className='dashboard-menu-btn-desktop d-none d-md-flex dark-theme',
        color='dark',
        n_clicks=0,
        title='Abrir menú',
        children=[html.I(className='bi bi-chevron-left')],
    )


def build_ada_navigation_mobile_trigger() -> dbc.Button:
    return dbc.Button(
        id=AdaNavigationIds.HEADER_MOBILE_TOGGLE,
        className='dashboard-menu-btn-mobile dark-theme',
        color='dark',
        n_clicks=0,
        title='Abrir menú',
        children=[html.I(className='bi bi-list')],
    )


def build_ada_navigation_offcanvas(menu: NavigationMenu) -> dbc.Offcanvas:
    return dbc.Offcanvas(
        id=AdaNavigationIds.HEADER_OFFCANVAS,
        title=_build_navigation_offcanvas_title(),
        is_open=False,
        placement='end',
        className='dashboard-main-offcanvas app-navigation-offcanvas',
        children=[
            html.Div(
                _build_navigation_menu_content(menu),
                id=AdaNavigationIds.HEADER_MENU_CONTENT,
                className='app-navigation-offcanvas-content',
            )
        ],
    )


def build_ada_navigation_offcanvas_from_services(services: ServiceRegistry) -> dbc.Offcanvas:
    return build_ada_navigation_offcanvas(resolve_navigation_from_services(services))


def _build_navigation_offcanvas_title() -> html.Div:
    return html.Div(
        className='app-navigation-offcanvas-title',
        children=[
            html.Div(
                className='app-navigation-offcanvas-title-icon',
                children=[html.I(className='bi bi-app-indicator')],
            ),
            html.Div(
                className='app-navigation-offcanvas-title-text',
                children=[
                    html.H5(
                        className='app-navigation-offcanvas-title-heading',
                        children=ADA_NAVIGATION_TITLE,
                    ),
                    html.P(
                        className='app-navigation-offcanvas-title-subtitle',
                        children=ADA_NAVIGATION_SUBTITLE,
                    ),
                ],
            ),
        ],
    )


def _build_navigation_menu_content(menu: NavigationMenu) -> html.Div:
    nodes = sorted(
        [*menu.links, *menu.groups],
        key=lambda node: (node.order, node.label, node.key),
    )
    return html.Div(
        className='app-navigation-content d-flex flex-column h-100',
        children=[
            _build_user_content(menu),
            _build_master_projects_button(),
            html.Div(className='app-navigation-soft-divider'),
            _build_navigation_nodes(nodes),
        ],
    )


def _build_user_content(menu: NavigationMenu) -> html.Div:
    user = menu.user
    return html.Div(
        className='app-navigation-user-card',
        children=[
            _build_user_avatar(user),
            html.Div(
                className='app-navigation-user-information',
                children=[
                    html.H4(
                        className='app-navigation-user-name',
                        children=user.display_name,
                    ),
                    _build_user_email(user.email),
                    html.Div(
                        className='app-navigation-user-profile',
                        style={'backgroundColor': user.profile_color},
                        children=[
                            html.I(className='bi bi-person-badge me-1'),
                            html.Span(user.profile_label),
                        ],
                    ),
                ],
            ),
        ],
    )


def _build_user_avatar(user: NavigationUser) -> html.Img | html.Div:
    if user.avatar_src is not None:
        return html.Img(
            className='app-navigation-user-avatar',
            src=user.avatar_src,
            alt=user.display_name,
        )
    return html.Div(
        className='app-navigation-user-avatar app-navigation-user-avatar-fallback',
        style={'backgroundColor': user.profile_color},
        title=user.display_name,
        children=user.avatar_text,
    )


def _build_user_email(email: str | None) -> html.P | None:
    if email is None:
        return None
    return html.P(className='app-navigation-user-email', children=email)


def _build_master_projects_button() -> html.A:
    return html.A(
        href=ADA_PROJECTS_URL,
        target='_blank',
        rel='noopener noreferrer',
        className='app-navigation-master-link text-decoration-none',
        children=[
            html.Span(
                className='app-navigation-master-link-label',
                children=[
                    html.I(className='bi bi-grid-1x2-fill me-2'),
                    html.Span(ADA_PROJECTS_LABEL),
                ],
            ),
            html.I(className='bi bi-box-arrow-up-right'),
        ],
    )


def _build_navigation_nodes(nodes: list[NavigationLink | NavigationGroup]) -> html.Div:
    if not nodes:
        return html.Div(
            className='app-navigation-empty text-muted small',
            children='No hay opciones de navegación disponibles.',
        )

    return html.Div(
        className='app-navigation-menu d-flex flex-column',
        children=[_build_node(node) for node in nodes],
    )


def _build_node(node: NavigationLink | NavigationGroup) -> html.Div | dcc.Link:
    if isinstance(node, NavigationGroup):
        return _build_group_node(node)
    return _build_link_node(node, is_child=False)


def _build_group_node(group: NavigationGroup) -> html.Div:
    return html.Div(
        className='app-navigation-root-item app-navigation-group {0}'.format(
            'disabled' if not group.enabled else ''
        ),
        children=[
            html.Button(
                id=AdaNavigationIds.group_toggle(group.key),
                type='button',
                className=_build_group_button_class_name(is_open=group.expanded),
                children=[
                    html.Span(
                        className='app-navigation-label d-flex align-items-center',
                        children=[
                            html.I(className=f'{group.icon} me-2') if group.icon else None,
                            html.Span(group.label),
                        ],
                    ),
                    html.I(className='bi bi-chevron-down app-navigation-group-chevron'),
                ],
                disabled=not group.enabled,
            ),
            dbc.Collapse(
                id=AdaNavigationIds.group_collapse(group.key),
                is_open=group.expanded,
                children=html.Div(
                    className='app-navigation-group-children d-flex flex-column',
                    children=[
                        _build_link_node(link, is_child=True)
                        for link in sorted(
                            group.links,
                            key=lambda item: (item.order, item.label, item.key),
                        )
                    ],
                ),
            ),
        ],
    )


def _build_link_node(link: NavigationLink, *, is_child: bool):
    link_child = html.Button(
        type='button',
        children=[
            html.I(className=f'{link.icon} me-2') if link.icon else None,
            html.Span(link.label),
        ],
        className=_build_link_button_class_name(is_child=is_child),
    )

    disabled = '' if link.enabled else 'disabled'
    class_name = 'app-navigation-link-wrapper d-block text-decoration-none {0}'.format(disabled)

    if link.new_tab or link.is_external:
        return html.A(
            link_child,
            href=link.href,
            target='_blank' if link.new_tab else '_self',
            rel='noopener noreferrer',
            className=class_name,
        )

    return dcc.Link(
        link_child,
        href=link.href,
        target='_self',
        className=class_name,
        refresh=link.force_reload,
    )


def _build_link_button_class_name(*, is_child: bool) -> str:
    class_names = [
        'app-navigation-button',
        'app-navigation-link',
    ]
    class_names.append('app-navigation-child-link' if is_child else 'app-navigation-root-link')
    return ' '.join(class_names)


def _build_group_button_class_name(*, is_open: bool) -> str:
    class_names = [
        'app-navigation-button',
        'app-navigation-group-button',
        'd-flex',
        'align-items-center',
        'justify-content-between',
    ]
    if is_open:
        class_names.append('app-navigation-group-button-open')
    return ' '.join(class_names)
