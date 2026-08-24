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


def test_production_runtime_has_no_compiled_tool_manifest_authority() -> None:
    paths = [*(ROOT / 'src').rglob('*.py')]
    content = '\n'.join(path.read_text(encoding='utf-8') for path in paths)

    assert 'INTEGRATED_OPERATIONS_MANIFEST' not in content
    assert 'MANIFEST = ' not in content
    assert 'COMPOSITION = ' not in content


def test_tool_projection_is_an_explicit_artifact_dependency() -> None:
    document = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))

    assert 'ada-configuration-tools==0.1.5' in document['project']['dependencies']
    assert document['tool']['uv']['sources']['ada-configuration-tools'] == {
        'path': 'wheels/ada_configuration_tools-0.1.5-py3-none-any.whl'
    }
