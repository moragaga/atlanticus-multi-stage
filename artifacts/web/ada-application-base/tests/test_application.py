from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import ada_application_base.application as application


def test_create_application_runtime_composes_deployment_modules(monkeypatch, tmp_path) -> None:
    deployment = Mock()
    deployment.bootstrap.modules = ('identity', 'users', 'navigation', 'activity')
    deployment.closed = False
    server = object()
    web = SimpleNamespace(server=server)
    captured = {}

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('ATLANTICUS_FLASK_SECRET_KEY', 'artifact-session-secret')

    def open_deployment(**kwargs):
        captured['deployment_call'] = kwargs
        return deployment

    monkeypatch.setattr(application, 'open_ada_web_deployment_runtime', open_deployment)

    def create_web(definition):
        captured['web_definition'] = definition
        return web

    monkeypatch.setattr(application, 'create_web_application', create_web)

    runtime = application.create_application_runtime()

    assert runtime.deployment is deployment
    assert runtime.web is web
    assert runtime.server is server
    assert 'identity_provider' not in captured['deployment_call']
    assert isinstance(captured['deployment_call']['environment'], application.EnvironmentReader)
    definition = captured['web_definition']
    assert definition.modules == deployment.bootstrap.modules
    assert definition.page_packages == ('ada_application_base.pages',)
    assert definition.publications_root == tmp_path / '.runtime' / 'assets'
    assert definition.flask_config == {'SECRET_KEY': 'artifact-session-secret'}


def test_create_application_runtime_closes_deployment_when_web_composition_fails(
    monkeypatch,
) -> None:
    deployment = Mock()
    deployment.bootstrap.modules = ()
    monkeypatch.setattr(
        application,
        'open_ada_web_deployment_runtime',
        lambda **_kwargs: deployment,
    )
    monkeypatch.setattr(
        application,
        'create_web_application',
        Mock(side_effect=RuntimeError('composition failed')),
    )

    with pytest.raises(RuntimeError, match='composition failed'):
        application.create_application_runtime()

    deployment.close.assert_called_once_with()


def test_application_runtime_close_delegates_to_deployment() -> None:
    deployment = Mock()
    runtime = application.AdaApplicationBaseRuntime(
        deployment=deployment,
        web=SimpleNamespace(server=object()),
    )

    runtime.close()

    deployment.close.assert_called_once_with()
