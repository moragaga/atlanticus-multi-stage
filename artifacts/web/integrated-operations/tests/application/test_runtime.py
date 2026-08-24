from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import integrated_operations.application.runtime as runtime_module


def test_runtime_wires_shared_deployment_operational_and_manager_composition(monkeypatch) -> None:
    environment_kind = object()
    backend_selection = object()
    runtime_projection = object()
    deployment_definition = SimpleNamespace()
    deployment = Mock()
    deployment.bootstrap.modules = ('identity', 'users', 'navigation', 'activity')
    deployment.infrastructure = object()
    manager_composition = object()
    manager_sharepoint = Mock()
    projection = object()
    resolution = object()
    application_composition = object()
    web = SimpleNamespace(server=object())
    captured = {}

    monkeypatch.setenv('ATLANTICUS_FLASK_SECRET_KEY', 'session-secret')
    monkeypatch.setattr(runtime_module, 'resolve_environment', lambda: environment_kind)
    monkeypatch.setattr(
        runtime_module, 'build_deployment_definition', lambda _env: deployment_definition
    )
    monkeypatch.setattr(
        runtime_module,
        '_resolve_optional_configuration_backends',
        lambda environment, web_environment: backend_selection,
    )
    monkeypatch.setattr(
        runtime_module,
        '_create_optional_runtime_projection',
        lambda selection, environment: runtime_projection,
    )

    def open_deployment(**kwargs):
        captured['deployment'] = kwargs
        return deployment

    monkeypatch.setattr(runtime_module, 'open_ada_web_deployment_runtime', open_deployment)

    def open_manager(**kwargs):
        captured['manager'] = kwargs
        return runtime_module._ManagerRuntimeComposition(
            manager_composition,
            manager_sharepoint,
        )

    monkeypatch.setattr(runtime_module, '_open_manager_composition', open_manager)
    monkeypatch.setattr(runtime_module, '_open_tool_projection', lambda _deployment: projection)

    def resolve_projection(repository):
        captured['projection_reader'] = repository
        return resolution

    monkeypatch.setattr(
        runtime_module,
        'resolve_projected_integrated_operations_manifest',
        resolve_projection,
    )

    def build_application_composition(**kwargs):
        captured['application_composition'] = kwargs
        return application_composition

    monkeypatch.setattr(
        runtime_module,
        'build_application_composition',
        build_application_composition,
    )

    def build_web_definition(**kwargs):
        captured['web_definition'] = kwargs
        return 'definition'

    monkeypatch.setattr(runtime_module, 'build_web_definition', build_web_definition)
    monkeypatch.setattr(runtime_module, 'create_web_application', lambda definition: web)

    result = runtime_module.create_application_runtime()

    assert result.deployment is deployment
    assert result.web is web
    assert result.server is web.server
    assert result.manager_sharepoint_infrastructure is manager_sharepoint
    assert captured['deployment']['definition'] is deployment_definition
    assert captured['deployment']['runtime_projection'] is runtime_projection
    assert captured['manager']['deployment'] is deployment
    assert captured['manager']['deployment_definition'] is deployment_definition
    assert captured['application_composition'] == {
        'tool_manifest_resolution': resolution,
        'manager': manager_composition,
    }
    assert captured['web_definition']['deployment_modules'] == deployment.bootstrap.modules
    assert captured['web_definition']['composition'] is application_composition
    assert captured['web_definition']['flask_config'] == {'SECRET_KEY': 'session-secret'}


def test_manager_composition_reuses_deployment_infrastructure(monkeypatch) -> None:
    selection = SimpleNamespace(requires_sharepoint=True)
    environment = object()
    web_environment = SimpleNamespace(is_production=True)
    sharepoint = object()
    deployment_definition = SimpleNamespace(
        sharepoint=object(),
        bindings=object(),
        configuration_filenames=object(),
    )
    deployment = SimpleNamespace(infrastructure=object())
    principal_provider = object()
    dependencies = object()
    surface_definition = object()
    surface = SimpleNamespace(web_modules=('manager-module',))
    binding = object()
    manager_composition = SimpleNamespace(surface=surface, principal_binding=binding)
    captured = {}

    def open_sharepoint(**kwargs):
        captured['sharepoint'] = kwargs
        return sharepoint

    monkeypatch.setattr(
        runtime_module,
        'open_configuration_manager_sharepoint_infrastructure',
        open_sharepoint,
    )
    monkeypatch.setattr(
        runtime_module,
        'EffectiveUserManagerPrincipalProvider',
        lambda: principal_provider,
    )

    def create_dependencies(**kwargs):
        captured['dependencies'] = kwargs
        return dependencies

    monkeypatch.setattr(
        runtime_module,
        'create_configuration_manager_dependencies',
        create_dependencies,
    )

    def build_surface(**kwargs):
        captured['surface'] = kwargs
        return surface_definition

    monkeypatch.setattr(runtime_module, 'build_configuration_manager_surface', build_surface)
    monkeypatch.setattr(runtime_module, 'ManagerSurface', lambda definition: surface)
    monkeypatch.setattr(
        runtime_module,
        'create_manager_principal_binding_module',
        lambda provider: binding,
    )

    def create_manager_composition(**kwargs):
        captured['manager_composition'] = kwargs
        return manager_composition

    monkeypatch.setattr(
        runtime_module,
        'create_ada_manager_surface_composition',
        create_manager_composition,
    )

    result = runtime_module._open_manager_composition(
        selection=selection,
        environment=environment,
        web_environment=web_environment,
        deployment_definition=deployment_definition,
        deployment=deployment,
    )

    assert result.sharepoint_infrastructure is sharepoint
    assert result.composition is manager_composition
    assert captured['manager_composition'] == {
        'surface': surface,
        'principal_binding': binding,
    }
    assert captured['dependencies']['infrastructure'] is deployment.infrastructure
    assert captured['dependencies']['sharepoint_infrastructure'] is sharepoint
    assert captured['dependencies']['principal_provider'] is principal_provider
    assert captured['dependencies']['force_publish_enabled'] is True
    assert captured['surface']['route_prefix'] == '/manager'


def test_manager_configuration_failure_does_not_block_operational_runtime(monkeypatch) -> None:
    sharepoint = Mock()
    monkeypatch.setattr(
        runtime_module,
        'open_configuration_manager_sharepoint_infrastructure',
        lambda **_kwargs: sharepoint,
    )
    monkeypatch.setattr(
        runtime_module,
        'EffectiveUserManagerPrincipalProvider',
        lambda: object(),
    )
    monkeypatch.setattr(
        runtime_module,
        'create_configuration_manager_dependencies',
        Mock(side_effect=runtime_module.WebConfigurationError('manager unavailable')),
    )

    result = runtime_module._open_manager_composition(
        selection=SimpleNamespace(requires_sharepoint=True),
        environment=object(),
        web_environment=SimpleNamespace(is_production=True),
        deployment_definition=SimpleNamespace(
            sharepoint=object(),
            bindings=object(),
            configuration_filenames=object(),
        ),
        deployment=SimpleNamespace(infrastructure=object()),
    )

    assert result.composition is None
    assert result.sharepoint_infrastructure is None
    sharepoint.close.assert_called_once_with()


def test_invalid_configuration_backend_selection_is_optional(monkeypatch) -> None:
    monkeypatch.setattr(
        runtime_module,
        'resolve_configuration_backend_selection',
        Mock(side_effect=runtime_module.WebConfigurationError('invalid configuration backend')),
    )

    result = runtime_module._resolve_optional_configuration_backends(object(), object())

    assert result is None


def test_invalid_configuration_backend_value_error_is_optional(monkeypatch) -> None:
    monkeypatch.setattr(
        runtime_module,
        'resolve_configuration_backend_selection',
        Mock(side_effect=ValueError('invalid optional configuration')),
    )

    result = runtime_module._resolve_optional_configuration_backends(object(), object())

    assert result is None


def test_runtime_closes_manager_and_deployment_when_web_composition_fails(monkeypatch) -> None:
    deployment = Mock()
    deployment.bootstrap.modules = ()
    manager_sharepoint = Mock()
    monkeypatch.setattr(runtime_module, 'resolve_environment', lambda: object())
    monkeypatch.setattr(runtime_module, 'build_deployment_definition', lambda _env: object())
    monkeypatch.setattr(
        runtime_module,
        '_resolve_optional_configuration_backends',
        lambda _environment, _web_environment: None,
    )
    monkeypatch.setattr(
        runtime_module,
        '_create_optional_runtime_projection',
        lambda _selection, _environment: None,
    )
    monkeypatch.setattr(
        runtime_module, 'open_ada_web_deployment_runtime', lambda **_kwargs: deployment
    )
    monkeypatch.setattr(
        runtime_module,
        '_open_manager_composition',
        lambda **_kwargs: runtime_module._ManagerRuntimeComposition(
            None,
            manager_sharepoint,
        ),
    )
    monkeypatch.setattr(runtime_module, '_open_tool_projection', lambda _deployment: object())
    monkeypatch.setattr(
        runtime_module,
        'resolve_projected_integrated_operations_manifest',
        lambda _repository: object(),
    )
    monkeypatch.setattr(
        runtime_module,
        'build_application_composition',
        lambda **_kwargs: object(),
    )
    monkeypatch.setattr(runtime_module, 'build_web_definition', lambda **_kwargs: 'definition')
    monkeypatch.setattr(
        runtime_module,
        'create_web_application',
        Mock(side_effect=RuntimeError('composition failed')),
    )

    with pytest.raises(RuntimeError, match='composition failed'):
        runtime_module.create_application_runtime()

    manager_sharepoint.close.assert_called_once_with()
    deployment.close.assert_called_once_with()


def test_runtime_close_releases_manager_before_deployment() -> None:
    calls = []
    manager_sharepoint = Mock()
    manager_sharepoint.close.side_effect = lambda: calls.append('manager')
    deployment = Mock()
    deployment.close.side_effect = lambda: calls.append('deployment')
    runtime = runtime_module.IntegratedOperationsApplicationRuntime(
        deployment=deployment,
        web=SimpleNamespace(server=object()),
        manager_sharepoint_infrastructure=manager_sharepoint,
    )

    runtime.close()

    assert calls == ['manager', 'deployment']
