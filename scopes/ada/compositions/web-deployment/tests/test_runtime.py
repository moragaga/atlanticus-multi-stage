import pytest

import ada.compositions.web_deployment.models as models_module
import ada.compositions.web_deployment.runtime as runtime_module
from ada.compositions.web_bootstrap import AdaCosmosBindings
from ada.compositions.web_deployment import (
    AdaWebDeploymentDefinition,
    AdaWebDeploymentError,
    open_ada_web_deployment_runtime,
)
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


def test_worker_runtime_requires_only_cosmos_environment_and_owns_lifecycle(monkeypatch) -> None:
    events = []

    class FakeInfrastructure:
        def __init__(self, *, cosmos_connections, sharepoint=None):
            self.cosmos_connections = cosmos_connections
            self.sharepoint = sharepoint
            events.append(('created', tuple(cosmos_connections), sharepoint))

        def open(self):
            events.append('open')

        def close(self):
            events.append('close')

    class FakeBootstrap:
        pass

    fake_bootstrap = FakeBootstrap()
    monkeypatch.setattr(runtime_module, 'WebRuntimeInfrastructure', FakeInfrastructure)
    monkeypatch.setattr(models_module, 'WebRuntimeInfrastructure', FakeInfrastructure)
    monkeypatch.setattr(models_module, 'AdaWebBootstrap', FakeBootstrap)

    def fake_bootstrap_factory(**kwargs):
        events.append(
            (
                'bootstrap',
                kwargs['bindings'].users,
                kwargs['environment'].value,
                kwargs['bootstrap_admin_principal'],
            )
        )
        return fake_bootstrap

    monkeypatch.setattr(runtime_module, 'create_ada_web_bootstrap', fake_bootstrap_factory)

    runtime = open_ada_web_deployment_runtime(
        definition=_definition(),
        metadata=object(),
        environment=EnvironmentReader(
            {
                'COSMOS_ENDPOINT': 'https://example.documents.azure.com/',
                'COSMOS_KEY': 'secret',
                'COSMOS_DATABASE': 'ada-runtime',
                'ATLANTICUS_ENVIRONMENT': 'production',
                'ATLANTICUS_BOOTSTRAP_ADMIN': 'Admin@Example.com',
            }
        ),
    )

    assert runtime.bootstrap is fake_bootstrap
    assert runtime.infrastructure.cosmos_connections['application'].database_name == 'ada-runtime'
    assert runtime.closed is False
    runtime.close()
    runtime.close()
    assert runtime.closed is True
    assert events == [
        ('created', ('application',), None),
        'open',
        ('bootstrap', 'application', 'production', 'admin@example.com'),
        'close',
    ]


def test_worker_runtime_closes_infrastructure_when_bootstrap_fails(monkeypatch) -> None:
    events = []

    class FakeInfrastructure:
        def __init__(self, *, cosmos_connections, sharepoint=None):
            del cosmos_connections, sharepoint

        def open(self):
            events.append('open')

        def close(self):
            events.append('close')

    monkeypatch.setattr(runtime_module, 'WebRuntimeInfrastructure', FakeInfrastructure)

    def fail_bootstrap(**kwargs):
        del kwargs
        raise RuntimeError('bootstrap failed')

    monkeypatch.setattr(runtime_module, 'create_ada_web_bootstrap', fail_bootstrap)

    with pytest.raises(RuntimeError, match='bootstrap failed'):
        open_ada_web_deployment_runtime(
            definition=_definition(),
            metadata=object(),
            environment=EnvironmentReader(
                {
                    'COSMOS_ENDPOINT': 'https://example.documents.azure.com/',
                    'COSMOS_KEY': 'secret',
                    'COSMOS_DATABASE': 'ada-runtime',
                }
            ),
        )

    assert events == ['open', 'close']


def test_closed_runtime_cannot_be_reentered(monkeypatch) -> None:
    class FakeInfrastructure:
        def close(self):
            return None

    class FakeBootstrap:
        pass

    monkeypatch.setattr(models_module, 'WebRuntimeInfrastructure', FakeInfrastructure)
    monkeypatch.setattr(models_module, 'AdaWebBootstrap', FakeBootstrap)
    runtime = models_module.AdaWebDeploymentRuntime(
        infrastructure=FakeInfrastructure(),
        bootstrap=FakeBootstrap(),
    )
    runtime.close()

    with pytest.raises(AdaWebDeploymentError, match='runtime is closed'):
        runtime.__enter__()
