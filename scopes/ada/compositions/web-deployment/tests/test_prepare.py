import pytest

import ada.compositions.web_deployment.prepare as prepare_module
from ada.compositions.web_bootstrap import AdaConfigurationFilenames, AdaCosmosBindings
from ada.compositions.web_deployment import AdaWebDeploymentDefinition, prepare_ada_web_deployment
from atlanticus.web.compositions.runtime_infrastructure import (
    CosmosConnectionEnvironmentDefinition,
    SharePointEnvironmentDefinition,
)
from atlanticus.web.environment import EnvironmentReader


def _definition() -> AdaWebDeploymentDefinition:
    return AdaWebDeploymentDefinition(
        cosmos_connections=(
            CosmosConnectionEnvironmentDefinition(
                name='application',
                endpoint_variable='COSMOS_ENDPOINT',
                key_variable='COSMOS_KEY',
                database_name_variable='COSMOS_DATABASE',
            ),
        ),
        bindings=AdaCosmosBindings(
            users='application',
            activity='application',
            navigation='application',
            tools='application',
        ),
        sharepoint=SharePointEnvironmentDefinition(
            read_endpoint_variable='SP_READ',
            write_endpoint_variable='SP_WRITE',
            root_path_variable='SP_ROOT',
            tool_path_variable='SP_TOOL',
        ),
    )


def _environment() -> EnvironmentReader:
    return EnvironmentReader(
        {
            'COSMOS_ENDPOINT': 'https://example.documents.azure.com/',
            'COSMOS_KEY': 'secret',
            'COSMOS_DATABASE': 'ada-deployment',
            'SP_READ': 'https://power.example.com/read/invoke?sig=read',
            'SP_WRITE': 'https://power.example.com/write/invoke?sig=write',
            'SP_ROOT': 'conciencia_situacional',
            'SP_TOOL': 'operaciones_integradas',
        }
    )


def test_prepare_resolves_environment_then_provisions_and_synchronizes(monkeypatch) -> None:
    events = []
    provisioning_result = object()
    configuration = object()
    synchronization_result = object()

    class FakeInfrastructure:
        def __init__(self, *, cosmos_connections, sharepoint):
            self.cosmos_connections = cosmos_connections
            self.sharepoint = sharepoint
            events.append(('created', tuple(cosmos_connections)))

        def open(self):
            events.append('open')

        def close(self):
            events.append('close')

    def fake_ensure(*, cosmos_connections, bindings, create_databases_if_missing):
        events.append(
            (
                'ensure',
                cosmos_connections['application'].database_name,
                bindings.users,
                create_databases_if_missing,
            )
        )
        return provisioning_result

    def fake_backends(*, infrastructure, bindings, filenames):
        assert isinstance(infrastructure, FakeInfrastructure)
        events.append(('backends', bindings.navigation, filenames.users))
        return configuration

    def fake_sync(*, configuration: object, actor: str):
        events.append(('sync', configuration, actor))
        return synchronization_result

    monkeypatch.setattr(prepare_module, 'WebRuntimeInfrastructure', FakeInfrastructure)
    monkeypatch.setattr(prepare_module, 'ensure_ada_cosmos_infrastructure', fake_ensure)
    monkeypatch.setattr(prepare_module, 'create_ada_configuration_backends', fake_backends)
    monkeypatch.setattr(prepare_module, 'synchronize_ada_access_projections', fake_sync)

    result = prepare_ada_web_deployment(
        definition=_definition(),
        environment=_environment(),
        create_databases_if_missing=True,
        actor='deployment-test',
    )

    assert result.provisioning is provisioning_result
    assert result.synchronization is synchronization_result
    assert events == [
        ('ensure', 'ada-deployment', 'application', True),
        ('created', ('application',)),
        'open',
        ('backends', 'application', 'users_configuration.json.gz'),
        ('sync', configuration, 'deployment-test'),
        'close',
    ]


def test_prepare_closes_sync_infrastructure_when_synchronization_fails(monkeypatch) -> None:
    events = []

    class FakeInfrastructure:
        def __init__(self, *, cosmos_connections, sharepoint):
            del cosmos_connections, sharepoint

        def open(self):
            events.append('open')

        def close(self):
            events.append('close')

    monkeypatch.setattr(prepare_module, 'WebRuntimeInfrastructure', FakeInfrastructure)
    monkeypatch.setattr(
        prepare_module,
        'ensure_ada_cosmos_infrastructure',
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        prepare_module,
        'create_ada_configuration_backends',
        lambda **kwargs: object(),
    )

    def fail_sync(**kwargs):
        del kwargs
        raise RuntimeError('sync failed')

    monkeypatch.setattr(prepare_module, 'synchronize_ada_access_projections', fail_sync)

    with pytest.raises(RuntimeError, match='sync failed'):
        prepare_ada_web_deployment(
            definition=_definition(),
            environment=_environment(),
        )

    assert events == ['open', 'close']


def test_prepare_passes_runtime_selected_filenames_to_configuration_backends(monkeypatch) -> None:
    observed = {}

    class FakeInfrastructure:
        def __init__(self, *, cosmos_connections, sharepoint):
            del cosmos_connections, sharepoint

        def open(self):
            return None

        def close(self):
            return None

    monkeypatch.setattr(prepare_module, 'WebRuntimeInfrastructure', FakeInfrastructure)
    monkeypatch.setattr(
        prepare_module,
        'ensure_ada_cosmos_infrastructure',
        lambda **kwargs: object(),
    )

    def fake_backends(*, infrastructure, bindings, filenames):
        del infrastructure, bindings
        observed['filenames'] = filenames
        return object()

    monkeypatch.setattr(prepare_module, 'create_ada_configuration_backends', fake_backends)
    monkeypatch.setattr(
        prepare_module,
        'synchronize_ada_access_projections',
        lambda **kwargs: object(),
    )

    base = _definition()
    definition = AdaWebDeploymentDefinition(
        cosmos_connections=base.cosmos_connections,
        bindings=base.bindings,
        sharepoint=base.sharepoint,
        configuration_filenames=AdaConfigurationFilenames(
            users='__e2e_users.json.gz',
            navigation='__e2e_navigation.json.gz',
            tools='__e2e_tools.json.gz',
        ),
    )

    prepare_ada_web_deployment(
        definition=definition,
        environment=_environment(),
    )

    assert observed['filenames'] == definition.configuration_filenames
