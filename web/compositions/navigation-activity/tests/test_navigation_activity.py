from atlanticus.web.compositions.navigation_activity import (
    NavigationActivityRouteResolver,
    create_navigation_activity_route_resolver,
)
from atlanticus.web.navigation.api import NavigationDefinition, NavigationLinkDefinition
from atlanticus.web.navigation.definition import (
    NAVIGATION_DEFINITION_PROVIDER_SERVICE_KEY,
    NavigationDefinitionProvider,
)
from atlanticus.web.services import ServiceRegistry


def _provider() -> NavigationDefinitionProvider:
    return NavigationDefinitionProvider(
        lambda: NavigationDefinition(
            links=(
                NavigationLinkDefinition(
                    key='alarms',
                    label='Alarmas',
                    href='/alarms',
                    allowed_profiles=('operator',),
                ),
            )
        )
    )


def test_navigation_activity_uses_stable_route_key() -> None:
    resolver = NavigationActivityRouteResolver(definition_provider=_provider())

    route = resolver.resolve('/alarms/')

    assert route.route_key == 'alarms'
    assert route.pathname == '/alarms'
    assert route.is_application_home is False


def test_navigation_activity_falls_back_for_unconfigured_unrestricted_routes() -> None:
    resolver = NavigationActivityRouteResolver(definition_provider=_provider())

    route = resolver.resolve('/diagnostics')

    assert route.route_key == '/diagnostics'
    assert route.pathname == '/diagnostics'


def test_navigation_activity_marks_root_as_application_home() -> None:
    resolver = NavigationActivityRouteResolver(definition_provider=_provider())

    route = resolver.resolve('/')

    assert route.route_key == '/'
    assert route.is_application_home is True


def test_navigation_activity_factory_resolves_provider_from_services() -> None:
    services = ServiceRegistry()
    services.add(NAVIGATION_DEFINITION_PROVIDER_SERVICE_KEY, _provider())

    resolver = create_navigation_activity_route_resolver(services)

    assert resolver.resolve('/alarms').route_key == 'alarms'
