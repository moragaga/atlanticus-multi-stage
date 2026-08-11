# Menú resuelto de prueba para validar el contrato transversal.
from atlanticus.web.navigation import (
    NavigationGroup,
    NavigationLink,
    NavigationMenu,
    NavigationUser,
)


def build_reference_navigation() -> NavigationMenu:
    return NavigationMenu(
        user=NavigationUser(
            display_name='Usuario Atlanticus',
            email='usuario@local.atlanticus',
            profile='Local',
            initials='UA',
        ),
        links=(NavigationLink(key='home', label='Inicio', href='/', order=0),),
        groups=(
            NavigationGroup(
                key='reference',
                label='Reference',
                order=10,
                links=(NavigationLink(key='status', label='Status', href='/status'),),
            ),
        ),
    )
