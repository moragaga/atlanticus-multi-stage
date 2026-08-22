import ast
import tomllib
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[1]
SOURCE_ROOT = PACKAGE_ROOT / 'src'
COMMENTED_ROOT = PACKAGE_ROOT / 'commented'


def test_package_dependencies_are_limited_to_existing_contract_layers() -> None:
    pyproject = tomllib.loads((PACKAGE_ROOT / 'pyproject.toml').read_text())

    assert pyproject['project']['dependencies'] == [
        'ada-composition-web-bootstrap==0.1.6',
        'atlanticus-web==0.1.0',
        'atlanticus-web-composition-runtime-infrastructure==0.1.0',
    ]


def test_deployment_resolves_only_web_environment_and_bootstrap_access_policy() -> None:
    source = '\n'.join(path.read_text() for path in SOURCE_ROOT.rglob('*.py'))

    assert 'ConfigurationBootstrap' not in source
    assert 'KeyVault' not in source
    assert 'ResolvedConfiguration' not in source
    assert 'ATLANTICUS_COSMOS_' not in source
    assert 'ATLANTICUS_SHAREPOINT_' not in source
    assert 'ATLANTICUS_IDENTITY_PROVIDER' not in source
    assert 'ATLANTICUS_ENVIRONMENT' in source
    assert 'ATLANTICUS_BOOTSTRAP_ADMIN' in source


def test_worker_runtime_does_not_include_sharepoint_or_provisioning() -> None:
    source = (SOURCE_ROOT / 'ada/compositions/web_deployment/runtime.py').read_text()

    assert 'resolve_sharepoint' not in source
    assert 'ensure_ada_cosmos_infrastructure' not in source
    assert 'synchronize_ada_access_projections' not in source
    assert 'create_ada_configuration_backends' not in source


def test_deployment_does_not_construct_the_flask_dash_application() -> None:
    source = '\n'.join(path.read_text() for path in SOURCE_ROOT.rglob('*.py'))

    assert 'create_web_application' not in source
    assert 'WebApplicationDefinition' not in source


def test_commented_mirror_matches_productive_ast() -> None:
    source_files = sorted(path.relative_to(SOURCE_ROOT) for path in SOURCE_ROOT.rglob('*.py'))
    commented_files = sorted(
        path.relative_to(COMMENTED_ROOT) for path in COMMENTED_ROOT.rglob('*.py')
    )

    assert source_files == commented_files
    for relative_path in source_files:
        productive = ast.dump(
            ast.parse((SOURCE_ROOT / relative_path).read_text()),
            include_attributes=False,
        )
        commented = ast.dump(
            ast.parse((COMMENTED_ROOT / relative_path).read_text()),
            include_attributes=False,
        )
        assert commented == productive
