import ast
from pathlib import Path


def test_application_host_does_not_own_sharepoint_or_cosmos_contracts() -> None:
    root = Path(__file__).parents[1] / 'src/ada/applications/configuration_manager'
    product = '\n'.join(path.read_text(encoding='utf-8') for path in root.glob('*.py'))

    assert 'SharePoint' not in product
    assert 'Cosmos' not in product


def test_application_host_does_not_own_manager_module_workflows() -> None:
    root = Path(__file__).parents[1] / 'src/ada/applications/configuration_manager'
    application = (root / 'application.py').read_text(encoding='utf-8')

    assert 'ToolManagerWorkflowAdapter' not in application
    assert 'KpiManagerWorkflowAdapter' not in application
    assert 'UsersManagerWorkflowAdapter' not in application
    assert 'NavigationManagerWorkflowAdapter' not in application
    assert 'ManagerModule(' not in application
    assert 'build_configuration_manager_surface' in application


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
