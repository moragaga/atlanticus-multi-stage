# Espejo comentado: definición global de navegación independiente del usuario.
from atlanticus.web.navigation import (
    NavigationDefinition,
    NavigationGroupDefinition,
    NavigationLinkDefinition,
)


def build_reference_navigation() -> NavigationDefinition:
    return NavigationDefinition(
        links=(
            NavigationLinkDefinition(
                key='home',
                label='Home',
                href='/',
                order=0,
                icon='home',
            ),
        ),
        groups=(
            NavigationGroupDefinition(
                key='main',
                label='Main',
                order=10,
                icon='folder',
                links=(
                    NavigationLinkDefinition(
                        key='status',
                        label='Status',
                        href='/status',
                    ),
                ),
            ),
        ),
    )
