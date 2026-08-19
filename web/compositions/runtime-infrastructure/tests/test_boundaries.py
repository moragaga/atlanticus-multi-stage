import ast
import tomllib
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[1]
SOURCE_ROOT = PACKAGE_ROOT / 'src'
COMMENTED_ROOT = PACKAGE_ROOT / 'commented'


def test_package_declares_only_composition_level_dependencies() -> None:
    pyproject = tomllib.loads((PACKAGE_ROOT / 'pyproject.toml').read_text())

    assert pyproject['project']['dependencies'] == [
        'atlanticus-configuration==0.1.0',
        'atlanticus-cosmos==0.1.0',
        'atlanticus-http==0.1.0',
        'atlanticus-web-composition-sharepoint-http==0.1.0',
    ]


def test_productive_code_does_not_read_environment_or_depend_on_ada() -> None:
    source = '\n'.join(path.read_text() for path in SOURCE_ROOT.rglob('*.py'))

    assert 'os.environ' not in source
    assert 'ada.' not in source
    assert 'ATLANTICUS_COSMOS_' not in source


def test_runtime_does_not_provision_cosmos() -> None:
    runtime_source = (
        SOURCE_ROOT / 'atlanticus/web/compositions/runtime_infrastructure/runtime.py'
    ).read_text()

    assert 'CosmosProvisioner' not in runtime_source
    assert 'ensure_database' not in runtime_source
    assert 'ensure_containers' not in runtime_source


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
