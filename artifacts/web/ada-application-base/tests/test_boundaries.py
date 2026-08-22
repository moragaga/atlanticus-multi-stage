import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_artifact_has_no_source_workspace_dependencies() -> None:
    document = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    assert document['tool']['uv']['find-links'] == ['wheels']
    sources = document['tool']['uv']['sources']

    assert sources
    for source in sources.values():
        assert set(source) == {'path'}
        assert source['path'].startswith('wheels/')
        assert '..' not in Path(source['path']).parts


def test_production_gunicorn_config_has_no_local_only_flags() -> None:
    content = (ROOT / 'gunicorn.conf.py').read_text(encoding='utf-8')

    assert 'preload_app' not in content
    assert 'debug' not in content
    assert 'resolve_gunicorn_capacity' in content
    assert 'post_worker_init' in content
    assert 'worker_exit' in content


def test_artifact_does_not_embed_secrets_or_signed_endpoints() -> None:
    paths = [
        ROOT / 'app.py',
        ROOT / 'gunicorn.conf.py',
        *(ROOT / 'src').rglob('*.py'),
    ]
    content = '\n'.join(path.read_text(encoding='utf-8') for path in paths)

    assert 'sig=' not in content
    assert 'AccountKey=' not in content
    assert 'ATLANTICUS_COSMOS_KEY=' not in content


def test_artifact_does_not_use_legacy_identity_selector() -> None:
    paths = [ROOT / 'app.py', *(ROOT / 'src').rglob('*.py')]
    content = '\n'.join(path.read_text(encoding='utf-8') for path in paths)

    assert 'ATLANTICUS_IDENTITY_PROVIDER' not in content
    assert 'resolve_identity_provider_key' not in content


def test_manager_is_embedded_without_standalone_manager_application() -> None:
    source = '\n'.join(path.read_text(encoding='utf-8') for path in (ROOT / 'src').rglob('*.py'))

    assert 'create_manager_application' not in source
    assert 'route_prefix=_MANAGER_ROUTE_PREFIX' in source
    assert "path='/manager'" in source
    assert "path_template='/manager/<module>'" in source
