import pytest

from atlanticus.web.errors import WebDefinitionError
from atlanticus.web.navigation import (
    NAVIGATION_SERVICE_KEY,
    NavigationGroup,
    NavigationLink,
    NavigationMenu,
    NavigationUser,
    create_navigation_module,
)
from atlanticus.web.services import ServiceRegistry


def _menu() -> NavigationMenu:
    return NavigationMenu(
        user=NavigationUser(
            display_name='John Doe',
            email='john.doe@local.atlanticus',
            profile='Administrator',
            initials='JD',
        ),
        links=(
            NavigationLink(key='home', label='Home', href='/', order=0, icon='home'),
        ),
        groups=(
            NavigationGroup(
                key='main',
                label='Main',
                order=10,
                icon='folder',
                links=(
                    NavigationLink(key='status', label='Status', href='/status'),
                ),
            ),
        ),
    )


def test_navigation_module_registers_resolved_menu_without_presentation() -> None:
    menu = _menu()
    module = create_navigation_module(menu)
    services = ServiceRegistry()

    assert module.name == 'navigation'
    assert module.register_callbacks is None
    assert module.asset_layers == ()

    assert module.register_services is not None
    module.register_services(services)
    assert services.require(NAVIGATION_SERVICE_KEY, NavigationMenu) is menu


def test_navigation_contract_supports_runtime_presentation_metadata() -> None:
    menu = _menu()

    assert menu.links[0].order == 0
    assert menu.links[0].icon == 'home'
    assert menu.groups[0].order == 10
    assert menu.groups[0].icon == 'folder'
    assert menu.groups[0].enabled is True


def test_navigation_rejects_unsafe_href_and_duplicate_keys() -> None:
    with pytest.raises(WebDefinitionError, match='HTTP'):
        NavigationLink(key='bad', label='Bad', href='javascript:alert(1)')

    link = NavigationLink(key='same', label='One', href='/one')
    with pytest.raises(WebDefinitionError, match='duplicated link keys'):
        NavigationGroup(key='main', label='Main', links=(link, link))

    with pytest.raises(WebDefinitionError, match='duplicated link keys'):
        NavigationMenu(
            user=NavigationUser(display_name='User', profile='Local', initials='U'),
            links=(link,),
            groups=(NavigationGroup(key='group', label='Group', links=(link,)),),
        )
