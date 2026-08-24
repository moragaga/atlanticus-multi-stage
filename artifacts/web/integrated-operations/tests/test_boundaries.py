import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLAT_MODULES = {
    'application.py',
    'definition.py',
    'identity.py',
    'prepare.py',
    'snapshot_repository.py',
    'tool.py',
    'wsgi.py',
}


def test_application_source_is_organized_by_responsibility() -> None:
    package = ROOT / 'src/integrated_operations'
    flat = {path.name for path in package.iterdir() if path.is_file()}

    assert not (flat & FLAT_MODULES)
    assert {
        'application',
        'deployment',
        'pages',
        'resources',
        'runtime',
        'tool',
    }.issubset({path.name for path in package.iterdir() if path.is_dir()})


def test_artifact_has_no_source_workspace_dependencies() -> None:
    document = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    assert document['tool']['uv']['find-links'] == ['wheels']
    sources = document['tool']['uv']['sources']
    assert sources
    for source in sources.values():
        assert set(source) == {'path'}
        assert source['path'].startswith('wheels/')
        assert '..' not in Path(source['path']).parts


def test_production_gunicorn_reuses_certified_worker_lifecycle() -> None:
    content = (ROOT / 'gunicorn.conf.py').read_text(encoding='utf-8')

    assert 'preload_app' not in content
    assert 'debug' not in content
    assert 'resolve_gunicorn_capacity' in content
    assert 'post_worker_init' in content
    assert 'worker_exit' in content


def test_artifact_does_not_embed_secrets_or_signed_endpoints() -> None:
    paths = [ROOT / 'app.py', ROOT / 'gunicorn.conf.py', *(ROOT / 'src').rglob('*.py')]
    content = '\n'.join(path.read_text(encoding='utf-8') for path in paths)

    assert 'sig=' not in content
    assert 'AccountKey=' not in content
    assert 'ATLANTICUS_COSMOS_KEY=' not in content


def test_artifact_does_not_use_legacy_identity_selector() -> None:
    paths = [ROOT / 'app.py', *(ROOT / 'src').rglob('*.py')]
    content = '\n'.join(path.read_text(encoding='utf-8') for path in paths)

    assert 'ATLANTICUS_IDENTITY_PROVIDER' not in content
    assert 'resolve_identity_provider_key' not in content


def test_production_runtime_has_no_global_compiled_tool_manifest_authority() -> None:
    paths = [*(ROOT / 'src').rglob('*.py')]
    content = '\n'.join(path.read_text(encoding='utf-8') for path in paths)

    assert 'MANIFEST = ' not in content
    assert 'COMPOSITION = ' not in content


def test_compiled_integrated_operations_manifest_is_used_only_as_runtime_baseline() -> None:
    content = (ROOT / 'src/integrated_operations/application/composition.py').read_text(
        encoding='utf-8'
    )

    assert 'INTEGRATED_OPERATIONS_MANIFEST' in content
    assert 'resolve_ada_surface' in content
    assert 'ToolManifestResolution.not_projected()' not in content


def test_tool_projection_is_an_explicit_artifact_dependency() -> None:
    document = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))

    assert 'ada-configuration-tools==0.1.5' in document['project']['dependencies']
    assert document['tool']['uv']['sources']['ada-configuration-tools'] == {
        'path': 'wheels/ada_configuration_tools-0.1.5-py3-none-any.whl'
    }


def test_unified_composition_uses_existing_manager_and_runtime_contracts() -> None:
    document = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    dependencies = set(document['project']['dependencies'])
    sources = document['tool']['uv']['sources']

    expected = {
        'ada-composition-configuration-manager': (
            '0.1.17',
            'ada_composition_configuration_manager-0.1.17-py3-none-any.whl',
        ),
        'ada-composition-manager-surface': (
            '0.1.0',
            'ada_composition_manager_surface-0.1.0-py3-none-any.whl',
        ),
        'atlanticus-web-manager': (
            '0.3.10',
            'atlanticus_web_manager-0.3.10-py3-none-any.whl',
        ),
        'atlanticus-web-composition-runtime-infrastructure': (
            '0.1.1',
            'atlanticus_web_composition_runtime_infrastructure-0.1.1-py3-none-any.whl',
        ),
    }
    for package, (version, filename) in expected.items():
        assert f'{package}=={version}' in dependencies
        assert sources[package] == {'path': f'wheels/{filename}'}


def test_manager_is_composed_as_optional_surface_not_operational_bootstrap_requirement() -> None:
    runtime = (ROOT / 'src/integrated_operations/application/runtime.py').read_text(
        encoding='utf-8'
    )
    models = (ROOT / 'src/integrated_operations/application/models.py').read_text(encoding='utf-8')

    assert 'AdaManagerSurfaceComposition | None' in models
    assert '_resolve_optional_configuration_backends' in runtime
    assert 'resolve_configuration_backend_selection' in runtime
    assert "_MANAGER_ROUTE_PREFIX = '/manager'" in runtime


def test_manager_presentation_is_owned_by_reusable_ada_manager_composition() -> None:
    presentation = (ROOT / 'src/integrated_operations/application/presentation.py').read_text(
        encoding='utf-8'
    )
    runtime = (ROOT / 'src/integrated_operations/application/runtime.py').read_text(
        encoding='utf-8'
    )

    assert 'create_ada_manager_surface_composition' in runtime
    assert 'composition.manager.build(services)' in presentation
    assert 'REFRESH_BUTTON_ID' not in presentation
    assert 'REFRESH_SIGNAL_ID' not in presentation
    assert 'build_ada_header' not in presentation
    assert 'ATLANTICUS_BRAND_MANIFEST' not in presentation


def test_unified_presentation_uses_one_dynamic_host_without_legacy_dual_hosts() -> None:
    presentation = (ROOT / 'src/integrated_operations/application/presentation.py').read_text(
        encoding='utf-8'
    )

    assert "SURFACE_HOST_ID = 'ada-unified-application-surface-host'" in presentation
    assert 'dcc.Loading(' in presentation
    assert 'build_ada_navigation_offcanvas_from_services' in presentation
    assert "_MANAGER_ROUTE_PREFIX = '/manager'" in presentation
    assert '_PAGE_HOST_ID' not in presentation
    assert '_MANAGER_HOST_ID' not in presentation
    assert 'hidden=True' not in presentation


def test_unified_presentation_uses_existing_navigation_contract() -> None:
    document = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))

    assert 'ada-ui-shell-navigation==0.1.0' in document['project']['dependencies']
    assert document['tool']['uv']['sources']['ada-ui-shell-navigation'] == {
        'path': 'wheels/ada_ui_shell_navigation-0.1.0-py3-none-any.whl'
    }


def test_operational_runtime_depends_on_generic_ada_surface_contract() -> None:
    document = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    composition = (ROOT / 'src/integrated_operations/application/composition.py').read_text(
        encoding='utf-8'
    )
    presentation = (ROOT / 'src/integrated_operations/application/presentation.py').read_text(
        encoding='utf-8'
    )

    assert 'ada-composition-surface==0.1.0' in document['project']['dependencies']
    assert document['tool']['uv']['sources']['ada-composition-surface'] == {
        'path': 'wheels/ada_composition_surface-0.1.0-py3-none-any.whl'
    }
    assert 'AdaSurfaceRegistry' in composition
    assert 'IntegratedOperationsSurfaceAdapter' in composition
    assert 'build_integrated_operations_tool' not in presentation
    assert 'composition.operational.build(services)' in presentation
    assert "'data-ada-surface-adapter': composition.operational.adapter_key" in presentation
