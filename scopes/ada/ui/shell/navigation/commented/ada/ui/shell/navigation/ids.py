# Espejo comentado: misma lógica productiva; comentarios en español.
from __future__ import annotations


class AdaNavigationIds:
    HEADER_OFFCANVAS = 'app-header-offcanvas'
    HEADER_MENU_CONTENT = 'app-header-menu-content'
    HEADER_MOBILE_TOGGLE = 'app-header-mobile-toggle'
    HEADER_DESKTOP_TOGGLE = 'app-header-desktop-toggle'

    NAVIGATION_GROUP_TOGGLE = 'app-navigation-group-toggle'
    NAVIGATION_GROUP_COLLAPSE = 'app-navigation-group-collapse'

    @staticmethod
    def group_toggle(group_key: str) -> dict[str, str]:
        return {
            'type': AdaNavigationIds.NAVIGATION_GROUP_TOGGLE,
            'group_key': group_key,
        }

    @staticmethod
    def group_collapse(group_key: str) -> dict[str, str]:
        return {
            'type': AdaNavigationIds.NAVIGATION_GROUP_COLLAPSE,
            'group_key': group_key,
        }
