from atlanticus.web.navigation import (
    NavigationGroup,
    NavigationLink,
    NavigationMenu,
    NavigationUser,
)


def build_reference_navigation() -> NavigationMenu:
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
                        order=10,
                        icon='bi bi-card-list',
                    ),
                ),
            ),
        ),
    )
