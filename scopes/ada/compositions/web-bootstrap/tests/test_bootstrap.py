from datetime import UTC, datetime

from ada.compositions.web_bootstrap import (
    AdaCosmosBindings,
    AdaRuntimeProjection,
    create_ada_configuration_backends,
    create_ada_web_bootstrap,
)
from atlanticus.web.environment import WebEnvironment
from atlanticus.web.models import ApplicationMetadata
from atlanticus.web.navigation.api import (
    NavigationDefinition,
    NavigationDefinitionProvider,
    NavigationLinkDefinition,
)
from atlanticus.web.navigation.configuration import (
    NavigationConfigurationCatalog,
    NavigationLinkConfiguration,
)
from atlanticus.web.navigation.configuration.projection import NavigationConfigurationProjection
from atlanticus.web.users.profiles import ProfileCatalog, ProfileDefinition


class FakeCosmosClient:
    def __init__(self, items=None) -> None:
        self.items = items or {}

    def health_check(self) -> bool:
        return True

    def find_item(self, *, container_name, item_id, partition_key, include_metadata=False):
        del include_metadata
        return self.items.get((container_name, partition_key, item_id))

    def create_item(self, *, container_name, item, include_metadata=False):
        del include_metadata
        key = (container_name, item.get('partition_key', item['id']), item['id'])
        self.items[key] = dict(item)
        return dict(item)

    def upsert_item(self, *, container_name, item):
        key = (container_name, item.get('partition_key', item['id']), item['id'])
        self.items[key] = dict(item)
        return dict(item)

    def patch_item(self, **kwargs):
        del kwargs
        return {}

    def query_items(self, **kwargs):
        del kwargs
        return ()


class FakeSharePointGateway:
    def read(self, *, filename: str, relative_path: str) -> str | None:
        del filename, relative_path
        return None

    def write(self, *, filename: str, relative_path: str, content: str) -> None:
        del filename, relative_path, content


class FakePaths:
    users_relative_path = 'conciencia_situacional/users'
    navigation_relative_path = 'conciencia_situacional/operaciones_integradas/navigation'
    tool_relative_path = 'conciencia_situacional/operaciones_integradas/tool'


class FakeInfrastructure:
    def __init__(self, clients, *, sharepoint_enabled: bool = True) -> None:
        self.clients = clients
        self._sharepoint_enabled = sharepoint_enabled
        self._gateway = FakeSharePointGateway()
        self.sharepoint_paths = FakePaths()

    def cosmos(self, connection_name: str):
        return self.clients[connection_name]

    def sharepoint(self):
        if not self._sharepoint_enabled:
            raise AssertionError('runtime bootstrap must not require SharePoint')
        return self._gateway


def _configuration_client() -> FakeCosmosClient:
    projection = NavigationConfigurationProjection.create(
        source_revision='navigation-source',
        projected_by='administrator',
        projected_at_utc=datetime(2026, 8, 19, 12, tzinfo=UTC),
        catalog=NavigationConfigurationCatalog(
            links=(NavigationLinkConfiguration(key='home', label='Inicio', href='/'),),
        ),
    )
    return FakeCosmosClient(
        {
            ('users_support', 'system', 'users'): {
                'id': 'users',
                'partition_key': 'system',
                'type': 'users_state',
                'schema_version': 2,
                'source_revision': 'users-source',
                'projection_status': 'ready',
                'projection_revision': 'users-projection',
                'projected_by': 'administrator',
                'projected_at_utc': '2026-08-19T12:00:00+00:00',
            },
            ('users_support', 'profiles', 'catalog'): {
                'id': 'catalog',
                'partition_key': 'profiles',
                'type': 'profile_catalog',
                'schema_version': 2,
                'source_revision': 'users-source',
                'administrator_background_color': '#112233',
                'administrator_text_color': '#FFFFFF',
                'guest_background_color': '#334455',
                'guest_text_color': '#FFFFFF',
                'custom_profiles': [
                    {
                        'key': 'operator',
                        'label': 'Operador',
                        'background_color': '#445566',
                        'text_color': '#FFFFFF',
                    }
                ],
            },
            ('configuration', 'navigation', 'navigation'): projection.to_document(
                item_id='navigation',
                partition_key='navigation',
            ),
        }
    )


def _bindings(connection: str = 'configuration') -> AdaCosmosBindings:
    return AdaCosmosBindings(
        users=connection,
        activity=connection,
        navigation=connection,
        tools=connection,
    )


def test_runtime_bootstrap_builds_projected_dependencies_without_sharepoint(monkeypatch) -> None:
    client = _configuration_client()
    infrastructure = FakeInfrastructure({'configuration': client}, sharepoint_enabled=False)
    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.bootstrap.WebRuntimeInfrastructure',
        FakeInfrastructure,
    )

    bootstrap = create_ada_web_bootstrap(
        metadata=ApplicationMetadata(
            application_id='ada-test',
            display_name='ADA Test',
            version='0.1.0',
        ),
        environment=WebEnvironment.PRODUCTION,
        infrastructure=infrastructure,
        bindings=_bindings(),
    )

    assert bootstrap.infrastructure is infrastructure
    assert bootstrap.profiles.require('operator') == ProfileDefinition(
        key='operator',
        label='Operador',
        background_color='#445566',
        text_color='#FFFFFF',
    )
    assert bootstrap.navigation_provider.current().links[0].key == 'home'
    assert [module.name for module in bootstrap.modules[:6]] == [
        'users',
        'identity',
        'navigation',
        'users-navigation',
        'navigation-authorization',
        'user-activity',
    ]


def test_configuration_backends_bind_sharepoint_paths_and_cosmos_projections(monkeypatch) -> None:
    client = _configuration_client()
    infrastructure = FakeInfrastructure({'configuration': client})
    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.bootstrap.WebRuntimeInfrastructure',
        FakeInfrastructure,
    )

    configuration = create_ada_configuration_backends(
        infrastructure=infrastructure,
        bindings=_bindings(),
    )

    assert configuration.users_source._settings.relative_path == 'conciencia_situacional/users'
    assert configuration.navigation_source._settings.relative_path == (
        'conciencia_situacional/operaciones_integradas/navigation'
    )
    assert configuration.tools_source._settings.relative_path == (
        'conciencia_situacional/operaciones_integradas/tool'
    )
    assert configuration.users_projection._client is client
    assert configuration.navigation_projection._client is client
    assert configuration.tools_projection._client is client


def test_runtime_bootstrap_reuses_same_cosmos_client_when_bindings_share_connection(
    monkeypatch,
) -> None:
    client = _configuration_client()
    infrastructure = FakeInfrastructure({'shared': client}, sharepoint_enabled=False)
    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.bootstrap.WebRuntimeInfrastructure',
        FakeInfrastructure,
    )

    bootstrap = create_ada_web_bootstrap(
        metadata=ApplicationMetadata('ada-test', 'ADA Test', '0.1.0'),
        environment=WebEnvironment.PRODUCTION,
        infrastructure=infrastructure,
        bindings=_bindings('shared'),
    )

    assert bootstrap.activity_repository._client is client
    assert bootstrap.users_source._gateway._client is client


def test_bootstrap_uses_solution_binding_for_each_cosmos_capability(monkeypatch) -> None:
    users_client = _configuration_client()
    navigation_client = _configuration_client()
    activity_client = FakeCosmosClient()
    tools_client = FakeCosmosClient()
    infrastructure = FakeInfrastructure(
        {
            'users-store': users_client,
            'navigation-store': navigation_client,
            'activity-store': activity_client,
            'tools-store': tools_client,
        }
    )
    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.bootstrap.WebRuntimeInfrastructure',
        FakeInfrastructure,
    )
    bindings = AdaCosmosBindings(
        users='users-store',
        activity='activity-store',
        navigation='navigation-store',
        tools='tools-store',
    )

    configuration = create_ada_configuration_backends(
        infrastructure=infrastructure,
        bindings=bindings,
    )
    runtime = create_ada_web_bootstrap(
        metadata=ApplicationMetadata('ada-test', 'ADA Test', '0.1.0'),
        environment=WebEnvironment.PRODUCTION,
        infrastructure=infrastructure,
        bindings=bindings,
    )

    assert configuration.users_projection._client is users_client
    assert configuration.navigation_projection._client is navigation_client
    assert configuration.tools_projection._client is tools_client
    assert runtime.activity_repository._client is activity_client


def test_runtime_bootstrap_local_can_use_injected_file_projection_without_navigation_cosmos(
    monkeypatch,
) -> None:
    users_client = _configuration_client()
    activity_client = FakeCosmosClient()
    infrastructure = FakeInfrastructure(
        {
            'users-store': users_client,
            'activity-store': activity_client,
        },
        sharepoint_enabled=False,
    )
    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.bootstrap.WebRuntimeInfrastructure',
        FakeInfrastructure,
    )
    profiles = ProfileCatalog(
        custom_profiles=(
            ProfileDefinition(
                key='operator',
                label='Operador',
                background_color='#445566',
            ),
        )
    )
    navigation_provider = NavigationDefinitionProvider(
        lambda: NavigationDefinition(
            links=(NavigationLinkDefinition(key='manager', label='Manager', href='/manager'),)
        )
    )

    bootstrap = create_ada_web_bootstrap(
        metadata=ApplicationMetadata('ada-test', 'ADA Test', '0.1.0'),
        environment=WebEnvironment.LOCAL,
        infrastructure=infrastructure,
        bindings=AdaCosmosBindings(
            users='users-store',
            activity='activity-store',
            navigation='navigation-store',
            tools='tools-store',
        ),
        runtime_projection=AdaRuntimeProjection(
            profiles=profiles,
            navigation_provider=navigation_provider,
        ),
    )

    assert bootstrap.identity_provider.key == 'local'
    assert bootstrap.users_source.__class__.__name__ == 'LocalUsersSource'
    assert bootstrap.profiles is profiles
    assert bootstrap.navigation_provider is navigation_provider
    assert bootstrap.navigation_provider.current().links[0].key == 'manager'
    assert bootstrap.activity_repository._client is activity_client


def test_runtime_bootstrap_local_uses_local_identity_and_users_with_projected_profiles(
    monkeypatch,
) -> None:
    client = _configuration_client()
    infrastructure = FakeInfrastructure({'configuration': client}, sharepoint_enabled=False)
    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.bootstrap.WebRuntimeInfrastructure',
        FakeInfrastructure,
    )

    bootstrap = create_ada_web_bootstrap(
        metadata=ApplicationMetadata('ada-test', 'ADA Test', '0.1.0'),
        environment=WebEnvironment.LOCAL,
        infrastructure=infrastructure,
        bindings=_bindings(),
    )

    assert bootstrap.identity_provider.key == 'local'
    assert bootstrap.users_source.__class__.__name__ == 'LocalUsersSource'
    assert bootstrap.profiles.require('operator').key == 'operator'
