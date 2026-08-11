from pathlib import Path

from atlanticus.web.navigation import NAVIGATION_SERVICE_KEY, NavigationMenu
from atlanticus_web_reference.application import build_definition
from atlanticus_web_reference.navigation import build_reference_navigation


def test_reference_definition_uses_navigation_service_and_dynamic_pages() -> None:
    definition = build_definition()
    modules = {module.name: module for module in definition.modules}
    identity = modules['identity']
    navigation = modules['navigation']
    reference = modules['reference']

    assert definition.metadata.application_id == 'atlanticus-web-reference'
    assert identity.register_services is not None
    assert identity.register_middlewares is not None
    assert identity.register_routes is not None
    assert navigation.register_services is not None
    assert navigation.register_callbacks is None
    assert navigation.asset_layers == ()
    assert reference.page_packages == ('atlanticus_web_reference.pages',)
    assert reference.register_services is not None
    assert reference.register_health_checks is not None
    assert reference.register_middlewares is not None
    assert reference.register_routes is not None
    assert reference.asset_layers[0].load_order == 900


def test_reference_navigation_is_resolved_before_web_composition() -> None:
    menu = build_reference_navigation()

    assert isinstance(menu, NavigationMenu)
    assert menu.links[0].href == '/'
    assert menu.groups[0].links[0].href == '/status'
    assert NAVIGATION_SERVICE_KEY == 'atlanticus.web.navigation.menu'


def test_reference_entrypoints_live_inside_the_application_package() -> None:
    package = Path(__file__).parents[1] / 'src' / 'atlanticus_web_reference'

    assert (package / '__main__.py').is_file()
    assert (package / 'wsgi.py').is_file()
    assert (package / 'pages' / 'home.py').is_file()
    assert (package / 'pages' / 'status.py').is_file()

