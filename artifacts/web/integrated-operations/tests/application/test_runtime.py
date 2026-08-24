from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import integrated_operations.application.runtime as runtime_module


def test_runtime_composes_deployment_and_projected_integrated_operations(monkeypatch) -> None:
    client = object()
    infrastructure = Mock()
    infrastructure.cosmos.return_value = client
    deployment = Mock()
    deployment.bootstrap.modules = ('identity', 'users', 'navigation', 'activity')
    deployment.bootstrap.infrastructure = infrastructure
    deployment.bootstrap.bindings = SimpleNamespace(tools='application')
    projection = object()
    resolution = object()
    web = SimpleNamespace(server=object())
    captured = {}

    monkeypatch.setenv('ATLANTICUS_FLASK_SECRET_KEY', 'session-secret')

    def open_deployment(**kwargs):
        captured['deployment'] = kwargs
        return deployment

    monkeypatch.setattr(runtime_module, 'open_ada_web_deployment_runtime', open_deployment)

    def projection_repository_factory(**kwargs):
        captured['projection_repository'] = kwargs
        return projection

    monkeypatch.setattr(
        runtime_module,
        'CosmosToolProjectionRepository',
        projection_repository_factory,
    )

    def resolve_projection(repository):
        captured['projection_reader'] = repository
        return resolution

    monkeypatch.setattr(
        runtime_module,
        'resolve_projected_integrated_operations_manifest',
        resolve_projection,
    )
    monkeypatch.setattr(
        runtime_module,
        'build_web_definition',
        lambda **kwargs: captured.setdefault('web_definition', kwargs) or 'definition',
    )
    monkeypatch.setattr(runtime_module, 'create_web_application', lambda definition: web)

    result = runtime_module.create_application_runtime()

    assert result.deployment is deployment
    assert result.web is web
    assert result.server is web.server
    assert 'identity_provider' not in captured['deployment']
    assert isinstance(captured['deployment']['environment'], runtime_module.EnvironmentReader)
    assert captured['projection_repository']['client'] is client
    assert captured['projection_reader'] is projection
    assert captured['web_definition']['deployment_modules'] == deployment.bootstrap.modules
    assert captured['web_definition']['tool_manifest_resolution'] is resolution
    assert captured['web_definition']['flask_config'] == {'SECRET_KEY': 'session-secret'}
    infrastructure.cosmos.assert_called_once_with('application')


def test_runtime_closes_deployment_when_web_composition_fails(monkeypatch) -> None:
    deployment = Mock()
    deployment.bootstrap.modules = ()
    deployment.bootstrap.infrastructure = Mock()
    deployment.bootstrap.bindings = SimpleNamespace(tools='application')
    monkeypatch.setattr(
        runtime_module, 'open_ada_web_deployment_runtime', lambda **_kwargs: deployment
    )
    monkeypatch.setattr(runtime_module, '_open_tool_projection', lambda _deployment: object())
    monkeypatch.setattr(
        runtime_module,
        'resolve_projected_integrated_operations_manifest',
        lambda _repository: object(),
    )
    monkeypatch.setattr(runtime_module, 'build_web_definition', lambda **_kwargs: 'definition')
    monkeypatch.setattr(
        runtime_module,
        'create_web_application',
        Mock(side_effect=RuntimeError('composition failed')),
    )

    with pytest.raises(RuntimeError, match='composition failed'):
        runtime_module.create_application_runtime()

    deployment.close.assert_called_once_with()


def test_runtime_close_delegates_to_deployment() -> None:
    deployment = Mock()
    runtime = runtime_module.IntegratedOperationsApplicationRuntime(
        deployment=deployment,
        web=SimpleNamespace(server=object()),
    )

    runtime.close()

    deployment.close.assert_called_once_with()
