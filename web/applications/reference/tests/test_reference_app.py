from pathlib import Path

from atlanticus.web.navigation.api import NavigationDefinition
from atlanticus.web.services import ServiceRegistry
from atlanticus_web_reference.application import build_definition
from atlanticus_web_reference.navigation import build_reference_navigation


def test_reference_definition_composes_users_identity_navigation_and_dynamic_pages(
    monkeypatch,
) -> None:
    monkeypatch.setenv('ATLANTICUS_ENVIRONMENT', 'local')
    definition = build_definition()
    modules = {module.name: module for module in definition.modules}
    users = modules['users']
    identity = modules['identity']
    navigation = modules['navigation']
    authorization = modules['navigation-authorization']
    activity = modules['user-activity']
    reference = modules['reference']

    assert definition.metadata.application_id == 'atlanticus-web-reference'
    assert users.register_services is not None
    assert identity.register_services is not None
    assert identity.register_middlewares is not None
    assert identity.register_routes is None
    assert navigation.register_services is not None
    assert navigation.register_callbacks is None
    assert navigation.asset_layers == ()
    assert authorization.register_middlewares is not None
    assert activity.register_services is not None
    assert activity.register_routes is not None
    assert activity.asset_layers[0].load_order == 650
    assert reference.page_packages == ('atlanticus_web_reference.pages',)
    assert reference.register_services is not None
    assert reference.register_health_checks is not None
    assert reference.register_middlewares is not None
    assert reference.register_routes is not None
    assert reference.asset_layers[0].load_order == 900


def test_reference_navigation_is_global_definition_not_user_specific_menu() -> None:
    definition = build_reference_navigation()

    assert isinstance(definition, NavigationDefinition)
    assert definition.links[0].href == '/'
    assert definition.groups[0].links[0].href == '/status'


def test_reference_entrypoints_live_inside_the_application_package() -> None:
    package = Path(__file__).parents[1] / 'src' / 'atlanticus_web_reference'

    assert (package / '__main__.py').is_file()
    assert (package / 'wsgi.py').is_file()
    assert (package / 'pages' / 'home.py').is_file()
    assert (package / 'pages' / 'status.py').is_file()


def test_reference_application_selects_app_service_provider(monkeypatch) -> None:
    monkeypatch.setenv('ATLANTICUS_ENVIRONMENT', 'production')

    definition = build_definition()
    identity = {module.name: module for module in definition.modules}['identity']
    services = ServiceRegistry()

    assert identity.register_services is not None
    identity.register_services(services)
