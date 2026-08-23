from pathlib import Path
from zipfile import ZipFile

COMPOSITION_VERSION = '0.1.14'
COMPOSITION_WHEEL_NAME = (
    f'ada_composition_configuration_manager-{COMPOSITION_VERSION}-py3-none-any.whl'
)


def test_configuration_manager_transport_contains_workspace_import_wiring() -> None:
    artifact = Path(__file__).resolve().parents[1]
    wheel = artifact / 'wheels' / COMPOSITION_WHEEL_NAME

    with ZipFile(wheel) as archive:
        backends = archive.read('ada/compositions/configuration_manager/backends.py').decode(
            'utf-8'
        )
        composition = archive.read('ada/compositions/configuration_manager/composition.py').decode(
            'utf-8'
        )
        workflows = archive.read('ada/compositions/configuration_manager/workflows.py').decode(
            'utf-8'
        )

    assert "_IMPORT_BACKEND_VARIABLE = 'ATLANTICUS_CONFIGURATION_IMPORT_BACKEND'" in backends
    assert 'class ConfigurationImportBackend(StrEnum):' in backends
    assert 'workspace_import: ConfigurationImportBackend' in backends
    assert 'ToolWorkspaceImportAdapter(tools_import_source)' in backends
    assert 'UsersWorkspaceImportAdapter(users_import_source)' in backends
    assert 'NavigationWorkspaceImportAdapter(navigation_import_source)' in backends
    assert 'TOOLS_WORKSPACE_IMPORT_SERVICE' in composition
    assert 'USERS_WORKSPACE_IMPORT_SERVICE' in composition
    assert 'NAVIGATION_WORKSPACE_IMPORT_SERVICE' in composition
    assert 'class ToolWorkspaceImportAdapter:' in workflows
    assert 'class UsersWorkspaceImportAdapter:' in workflows
    assert 'class NavigationWorkspaceImportAdapter:' in workflows
