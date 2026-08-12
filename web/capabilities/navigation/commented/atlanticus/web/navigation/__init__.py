# Espejo comentado: superficie pública de la capability transversal de navegación.
from atlanticus.web.navigation.models import (
    NavigationDefinition,
    NavigationGroup,
    NavigationGroupDefinition,
    NavigationLink,
    NavigationLinkDefinition,
    NavigationMenu,
    NavigationUser,
)
from atlanticus.web.navigation.module import create_navigation_module
from atlanticus.web.navigation.resolver import (
    NAVIGATION_DEFINITION_SERVICE_KEY,
    resolve_navigation,
    resolve_navigation_from_services,
    validate_navigation_definition,
)

__all__ = [
    'NAVIGATION_DEFINITION_SERVICE_KEY',
    'NavigationDefinition',
    'NavigationGroup',
    'NavigationGroupDefinition',
    'NavigationLink',
    'NavigationLinkDefinition',
    'NavigationMenu',
    'NavigationUser',
    'create_navigation_module',
    'resolve_navigation',
    'resolve_navigation_from_services',
    'validate_navigation_definition',
]
