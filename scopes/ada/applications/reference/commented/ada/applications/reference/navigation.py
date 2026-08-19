# Espejo comentado: definición de rutas de referencia para ADA.
from atlanticus.web.navigation.api import (
    NavigationDefinition,
    NavigationGroupDefinition,
    NavigationLinkDefinition,
)


def build_reference_navigation() -> NavigationDefinition:
    return NavigationDefinition(
        links=(
            NavigationLinkDefinition(
                key='home',
                label='Inicio',
                href='/',
                order=0,
                icon='bi bi-house',
            ),
        ),
        groups=(
            NavigationGroupDefinition(
                key='configuration',
                label='CONFIGURACIÓN',
                order=10,
                icon='bi bi-gear',
                links=(
                    NavigationLinkDefinition(
                        key='status',
                        label='Status',
                        href='/status',
                        order=10,
                        icon='bi bi-card-list',
                    ),
                ),
            ),
        ),
    )
