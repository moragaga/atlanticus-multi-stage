from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import ada_application_base.application as application


def _deployment_definition() -> SimpleNamespace:
    return SimpleNamespace(
        bindings='bindings',
        configuration_filenames='filenames',
        sharepoint='sharepoint-definition',
    )


def test_create_application_runtime_mounts_manager_in_same_web_runtime(
    monkeypatch, tmp_path
) -> None:
    deployment_definition = _deployment_definition()
    backend_selection = SimpleNamespace(requires_sharepoint=False)
    deployment = Mock()
    deployment.infrastructure = object()
    deployment.bootstrap.modules = ('identity', 'users', 'navigation', 'activity')
    server = object()
    web = SimpleNamespace(server=server)
    principal_provider = object()
    manager_dependencies = object()
    runtime_projection = object()
    surface_definition = object()
    manager_surface = SimpleNamespace(
        web_modules=('manager-services', 'manager-callbacks'),
        layout=lambda _services: object(),
    )
    captured = {}

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('ATLANTICUS_ENVIRONMENT', 'local')
    monkeypatch.setenv('ATLANTICUS_FLASK_SECRET_KEY', 'artifact-session-secret')
    monkeypatch.setattr(
        application,
        'build_deployment_definition',
        lambda _environment: deployment_definition,
    )
    monkeypatch.setattr(
        application,
        'resolve_configuration_backend_selection',
        lambda _environment, _web_environment: backend_selection,
    )

    def create_runtime_projection(**kwargs):
        captured['runtime_projection_call'] = kwargs
        return runtime_projection

    monkeypatch.setattr(
        application,
        'create_configuration_runtime_projection',
        create_runtime_projection,
    )

    def open_deployment(**kwargs):
        captured['deployment_call'] = kwargs
        return deployment

    monkeypatch.setattr(application, 'open_ada_web_deployment_runtime', open_deployment)

    def open_manager_sharepoint(**kwargs):
        captured['manager_sharepoint_call'] = kwargs
        return None

    monkeypatch.setattr(
        application,
        'open_configuration_manager_sharepoint_infrastructure',
        open_manager_sharepoint,
    )
    monkeypatch.setattr(
        application,
        'EffectiveUserManagerPrincipalProvider',
        lambda: principal_provider,
    )

    def create_manager_dependencies(**kwargs):
        captured['manager_dependencies_call'] = kwargs
        return manager_dependencies

    monkeypatch.setattr(
        application,
        'create_configuration_manager_dependencies',
        create_manager_dependencies,
    )

    def build_manager_surface(**kwargs):
        captured['surface_call'] = kwargs
        return surface_definition

    monkeypatch.setattr(
        application,
        'build_configuration_manager_surface',
        build_manager_surface,
    )
    monkeypatch.setattr(application, 'ManagerSurface', lambda _definition: manager_surface)
    monkeypatch.setattr(
        application,
        'create_manager_principal_binding_module',
        lambda provider: ('principal-binding', provider),
    )

    def create_web(definition):
        captured['web_definition'] = definition
        return web

    monkeypatch.setattr(application, 'create_web_application', create_web)

    runtime = application.create_application_runtime()

    assert runtime.deployment is deployment
    assert runtime.web is web
    assert runtime.server is server
    assert runtime.manager_sharepoint_infrastructure is None
    assert captured['runtime_projection_call']['selection'] is backend_selection
    assert captured['deployment_call']['runtime_projection'] is runtime_projection
    assert 'include_sharepoint' not in captured['deployment_call']
    assert captured['manager_sharepoint_call']['selection'] is backend_selection
    assert captured['manager_sharepoint_call']['definition'] == 'sharepoint-definition'
    assert captured['manager_dependencies_call']['selection'] is backend_selection
    assert captured['manager_dependencies_call']['infrastructure'] is deployment.infrastructure
    assert captured['manager_dependencies_call']['sharepoint_infrastructure'] is None
    assert captured['manager_dependencies_call']['bindings'] == 'bindings'
    assert captured['manager_dependencies_call']['filenames'] == 'filenames'
    assert captured['manager_dependencies_call']['principal_provider'] is principal_provider
    assert captured['manager_dependencies_call']['force_publish_enabled'] is False
    assert captured['surface_call'] == {
        'dependencies': manager_dependencies,
        'route_prefix': '/manager',
    }
    definition = captured['web_definition']
    assert definition.modules[:4] == deployment.bootstrap.modules
    assert ('principal-binding', principal_provider) in definition.modules
    assert 'manager-services' in definition.modules
    assert 'manager-callbacks' in definition.modules
    assert definition.modules[-1].name == 'ada-application-base-manager-host'
    assert definition.page_packages == ('ada_application_base.pages',)
    assert definition.publications_root == tmp_path / '.runtime' / 'assets'
    assert definition.flask_config == {'SECRET_KEY': 'artifact-session-secret'}


def test_create_application_runtime_opens_sharepoint_only_for_manager_history(monkeypatch) -> None:
    deployment_definition = _deployment_definition()
    backend_selection = SimpleNamespace(requires_sharepoint=True)
    deployment = Mock()
    deployment.infrastructure = object()
    deployment.bootstrap.modules = ()
    manager_sharepoint = Mock()
    captured = {}

    monkeypatch.setattr(
        application,
        'resolve_environment',
        lambda: SimpleNamespace(is_production=True),
    )
    monkeypatch.setattr(
        application,
        'build_deployment_definition',
        lambda _environment: deployment_definition,
    )
    monkeypatch.setattr(
        application,
        'resolve_configuration_backend_selection',
        lambda _environment, _web_environment: backend_selection,
    )
    monkeypatch.setattr(
        application,
        'create_configuration_runtime_projection',
        lambda **_kwargs: None,
    )

    def open_deployment(**kwargs):
        captured['deployment_call'] = kwargs
        return deployment

    monkeypatch.setattr(application, 'open_ada_web_deployment_runtime', open_deployment)

    def open_manager_sharepoint(**kwargs):
        captured['manager_sharepoint_call'] = kwargs
        return manager_sharepoint

    monkeypatch.setattr(
        application,
        'open_configuration_manager_sharepoint_infrastructure',
        open_manager_sharepoint,
    )

    def create_manager_dependencies(**kwargs):
        captured['manager_dependencies_call'] = kwargs
        raise RuntimeError('stop after manager infrastructure')

    monkeypatch.setattr(
        application,
        'create_configuration_manager_dependencies',
        create_manager_dependencies,
    )

    with pytest.raises(RuntimeError, match='stop after manager infrastructure'):
        application.create_application_runtime()

    assert 'include_sharepoint' not in captured['deployment_call']
    assert captured['manager_sharepoint_call']['selection'] is backend_selection
    assert captured['manager_sharepoint_call']['definition'] == 'sharepoint-definition'
    assert captured['manager_dependencies_call']['web_environment'].is_production is True
    assert captured['manager_dependencies_call']['force_publish_enabled'] is True
    manager_sharepoint.close.assert_called_once_with()
    deployment.close.assert_called_once_with()


def test_create_application_runtime_closes_manager_and_deployment_when_web_composition_fails(
    monkeypatch,
) -> None:
    deployment_definition = _deployment_definition()
    deployment = Mock()
    deployment.infrastructure = object()
    deployment.bootstrap.modules = ()
    manager_sharepoint = Mock()
    principal_provider = object()
    manager_surface = SimpleNamespace(web_modules=(), layout=lambda _services: object())

    monkeypatch.setattr(
        application,
        'build_deployment_definition',
        lambda _environment: deployment_definition,
    )
    monkeypatch.setattr(
        application,
        'resolve_configuration_backend_selection',
        lambda _environment, _web_environment: SimpleNamespace(requires_sharepoint=True),
    )
    monkeypatch.setattr(
        application,
        'create_configuration_runtime_projection',
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        application,
        'open_ada_web_deployment_runtime',
        lambda **_kwargs: deployment,
    )
    monkeypatch.setattr(
        application,
        'open_configuration_manager_sharepoint_infrastructure',
        lambda **_kwargs: manager_sharepoint,
    )
    monkeypatch.setattr(
        application,
        'EffectiveUserManagerPrincipalProvider',
        lambda: principal_provider,
    )
    monkeypatch.setattr(
        application,
        'create_configuration_manager_dependencies',
        lambda **_kwargs: object(),
    )
    monkeypatch.setattr(
        application,
        'build_configuration_manager_surface',
        lambda **_kwargs: object(),
    )
    monkeypatch.setattr(application, 'ManagerSurface', lambda _definition: manager_surface)
    monkeypatch.setattr(
        application,
        'create_manager_principal_binding_module',
        lambda _provider: Mock(name='principal-binding'),
    )
    monkeypatch.setattr(
        application,
        'create_web_application',
        Mock(side_effect=RuntimeError('composition failed')),
    )

    with pytest.raises(RuntimeError, match='composition failed'):
        application.create_application_runtime()

    manager_sharepoint.close.assert_called_once_with()
    deployment.close.assert_called_once_with()


def test_application_runtime_close_closes_manager_sharepoint_then_deployment() -> None:
    deployment = Mock()
    manager_sharepoint = Mock()
    runtime = application.AdaApplicationBaseRuntime(
        deployment=deployment,
        web=SimpleNamespace(server=object()),
        manager_sharepoint_infrastructure=manager_sharepoint,
    )

    runtime.close()

    manager_sharepoint.close.assert_called_once_with()
    deployment.close.assert_called_once_with()


def test_application_runtime_close_still_closes_deployment_when_manager_close_fails() -> None:
    deployment = Mock()
    manager_sharepoint = Mock()
    manager_sharepoint.close.side_effect = RuntimeError('manager close failed')
    runtime = application.AdaApplicationBaseRuntime(
        deployment=deployment,
        web=SimpleNamespace(server=object()),
        manager_sharepoint_infrastructure=manager_sharepoint,
    )

    with pytest.raises(RuntimeError, match='manager close failed'):
        runtime.close()

    deployment.close.assert_called_once_with()


def test_manager_routes_are_namespaced_under_manager() -> None:
    assert application._is_manager_route('/manager') is True
    assert application._is_manager_route('/manager/tools') is True
    assert application._is_manager_route('/manager/users') is True
    assert application._is_manager_route('/manager/navigation') is True
    assert application._is_manager_route('/') is False
    assert application._is_manager_route('/tools') is False
