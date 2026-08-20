from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import integrated_operations.application.runtime as runtime_module


def test_runtime_composes_deployment_and_integrated_operations(monkeypatch) -> None:
    deployment = Mock()
    deployment.bootstrap.modules = ('identity', 'users', 'navigation', 'activity')
    web = SimpleNamespace(server=object())
    captured = {}

    monkeypatch.setenv('ATLANTICUS_FLASK_SECRET_KEY', 'session-secret')
    monkeypatch.setattr(runtime_module, 'build_identity_provider', lambda: 'provider')

    def open_deployment(**kwargs):
        captured['deployment'] = kwargs
        return deployment

    monkeypatch.setattr(runtime_module, 'open_ada_web_deployment_runtime', open_deployment)
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
    assert captured['deployment']['identity_provider'] == 'provider'
    assert isinstance(captured['deployment']['environment'], runtime_module.EnvironmentReader)
    assert captured['web_definition']['deployment_modules'] == deployment.bootstrap.modules
    assert captured['web_definition']['flask_config'] == {'SECRET_KEY': 'session-secret'}


def test_runtime_closes_deployment_when_web_composition_fails(monkeypatch) -> None:
    deployment = Mock()
    deployment.bootstrap.modules = ()
    monkeypatch.setattr(runtime_module, 'build_identity_provider', lambda: 'provider')
    monkeypatch.setattr(
        runtime_module, 'open_ada_web_deployment_runtime', lambda **_kwargs: deployment
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
