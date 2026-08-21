import ast
from pathlib import Path


def test_configuration_manager_composition_does_not_own_web_application_host() -> None:
    root = Path(__file__).parents[1] / 'src/ada/compositions/configuration_manager'
    product = '\n'.join(path.read_text(encoding='utf-8') for path in root.glob('*.py'))

    assert 'create_web_application' not in product
    assert 'create_manager_application' not in product
    assert 'WebApplicationDefinition' not in product
    assert 'ApplicationMetadata' not in product
    assert 'DashSettings' not in product
    assert 'ManagerBrand' not in product
    assert 'ada.ui.' not in product


def test_commented_mirror_matches_productive_ast() -> None:
    package_root = Path(__file__).parents[1]
    source_root = package_root / 'src'
    commented_root = package_root / 'commented'
    source_files = sorted(path.relative_to(source_root) for path in source_root.rglob('*.py'))
    commented_files = sorted(
        path.relative_to(commented_root) for path in commented_root.rglob('*.py')
    )

    assert source_files == commented_files
    for relative_path in source_files:
        productive = ast.dump(
            ast.parse((source_root / relative_path).read_text(encoding='utf-8')),
            include_attributes=False,
        )
        commented = ast.dump(
            ast.parse((commented_root / relative_path).read_text(encoding='utf-8')),
            include_attributes=False,
        )
        assert commented == productive
