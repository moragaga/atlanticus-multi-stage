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

    assert 'ada-configuration-tools==0.1.11' in document['project']['dependencies']
    assert document['tool']['uv']['sources']['ada-configuration-tools'] == {
        'path': 'wheels/ada_configuration_tools-0.1.11-py3-none-any.whl'
    }


def test_kpi_projection_manager_is_an_explicit_artifact_dependency() -> None:
    document = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))

    assert 'ada-configuration-kpis==0.2.6' in document['project']['dependencies']
    assert document['tool']['uv']['sources']['ada-configuration-kpis'] == {
        'path': 'wheels/ada_configuration_kpis-0.2.6-py3-none-any.whl'
    }


def test_unified_composition_uses_existing_manager_runtime_and_application_contracts() -> None:
    document = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    dependencies = set(document['project']['dependencies'])
    sources = document['tool']['uv']['sources']

    expected = {
        'ada-composition-configuration-manager': (
            '0.1.24',
            'ada_composition_configuration_manager-0.1.24-py3-none-any.whl',
        ),
        'ada-composition-manager-surface': (
            '0.1.1',
            'ada_composition_manager_surface-0.1.1-py3-none-any.whl',
        ),
        'ada-composition-web-application': (
            '0.1.0',
            'ada_composition_web_application-0.1.0-py3-none-any.whl',
        ),
        'atlanticus-web-manager': (
            '0.3.11',
            'atlanticus_web_manager-0.3.11-py3-none-any.whl',
        ),
        'atlanticus-web-composition-runtime-infrastructure': (
            '0.1.1',
            'atlanticus_web_composition_runtime_infrastructure-0.1.1-py3-none-any.whl',
        ),
    }
    for package, (version, filename) in expected.items():
        assert f'{package}=={version}' in dependencies
        assert sources[package] == {'path': f'wheels/{filename}'}


def test_concrete_artifact_no_longer_owns_generic_application_host() -> None:
    application = ROOT / 'src/integrated_operations/application'
    composition = (application / 'composition.py').read_text(encoding='utf-8')

    assert not (application / 'models.py').exists()
    assert not (application / 'presentation.py').exists()
    assert not (application / 'layout.py').exists()
    assert 'AdaApplicationComposition' in composition
    assert 'build_ada_web_definition' in composition
    assert 'dcc.Location' not in composition
    assert 'dcc.Loading' not in composition
    assert 'build_ada_navigation_offcanvas_from_services' not in composition


def test_manager_is_optional_and_route_prefix_remains_concrete() -> None:
    runtime = (ROOT / 'src/integrated_operations/application/runtime.py').read_text(
        encoding='utf-8'
    )
    composition = (ROOT / 'src/integrated_operations/application/composition.py').read_text(
        encoding='utf-8'
    )

    assert 'AdaManagerSurfaceComposition | None' in runtime
    assert '_resolve_optional_configuration_backends' in runtime
    assert 'resolve_configuration_backend_selection' in runtime
    assert "MANAGER_ROUTE_PREFIX = '/manager'" in composition
    assert 'administration_route_prefix=MANAGER_ROUTE_PREFIX' in composition


def test_manager_and_operational_runtime_share_one_infrastructure_lifecycle() -> None:
    runtime = (ROOT / 'src/integrated_operations/application/runtime.py').read_text(
        encoding='utf-8'
    )

    assert 'open_configuration_manager_sharepoint_infrastructure' not in runtime
    assert 'manager_sharepoint_infrastructure' not in runtime
    assert 'sharepoint=sharepoint' in runtime
    assert 'sharepoint_infrastructure=(' in runtime
    assert 'deployment.infrastructure if selection.requires_sharepoint else None' in runtime
    assert 'self.deployment.close()' in runtime


def test_manager_presentation_remains_owned_by_reusable_manager_composition() -> None:
    runtime = (ROOT / 'src/integrated_operations/application/runtime.py').read_text(
        encoding='utf-8'
    )
    composition = (ROOT / 'src/integrated_operations/application/composition.py').read_text(
        encoding='utf-8'
    )

    assert 'create_ada_manager_surface_composition' in runtime
    assert 'REFRESH_BUTTON_ID' not in composition
    assert 'REFRESH_SIGNAL_ID' not in composition
    assert 'build_ada_header' not in composition
    assert 'ATLANTICUS_BRAND_MANIFEST' not in composition


def test_operational_runtime_keeps_concrete_registry_outside_generic_application() -> None:
    document = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    composition = (ROOT / 'src/integrated_operations/application/composition.py').read_text(
        encoding='utf-8'
    )

    assert 'ada-composition-surface==0.1.0' in document['project']['dependencies']
    assert document['tool']['uv']['sources']['ada-composition-surface'] == {
        'path': 'wheels/ada_composition_surface-0.1.0-py3-none-any.whl'
    }
    assert 'AdaSurfaceRegistry' in composition
    assert 'IntegratedOperationsSurfaceAdapter' in composition
    assert 'build_integrated_operations_tool' not in composition


def test_unified_presentation_assets_left_concrete_integrated_operations_css() -> None:
    css = (ROOT / 'src/integrated_operations/resources/css/10-integrated-operations.css').read_text(
        encoding='utf-8'
    )

    assert '.integrated-operations' in css
    assert '.ada-unified-application' not in css
    assert '#react-entry-point' not in css
