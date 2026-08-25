from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
WHEELS = ROOT / 'wheels'


def _read(wheel_name: str, member: str) -> str:
    with ZipFile(WHEELS / wheel_name) as archive:
        return archive.read(member).decode('utf-8')


def test_configuration_manager_transport_has_no_legacy_workspace_import_backend() -> None:
    wheel = 'ada_composition_configuration_manager-0.1.20-py3-none-any.whl'
    backends = _read(wheel, 'ada/compositions/configuration_manager/backends.py')
    composition = _read(wheel, 'ada/compositions/configuration_manager/composition.py')
    dependencies = _read(wheel, 'ada/compositions/configuration_manager/dependencies.py')
    workflows = _read(wheel, 'ada/compositions/configuration_manager/workflows.py')

    combined = '\n'.join((backends, composition, dependencies, workflows))
    assert 'ATLANTICUS_CONFIGURATION_IMPORT_BACKEND' not in combined
    assert 'ConfigurationImportBackend' not in combined
    assert 'WorkspaceImport' not in combined
    assert 'WORKSPACE_IMPORT_SERVICE' not in combined


def test_native_module_importers_remain_the_only_file_import_path() -> None:
    tools_layout = _read(
        'ada_configuration_tools-0.1.7-py3-none-any.whl',
        'ada/configuration/tools/web/layout.py',
    )
    tools_callbacks = _read(
        'ada_configuration_tools-0.1.7-py3-none-any.whl',
        'ada/configuration/tools/web/callbacks.py',
    )
    users_layout = _read(
        'atlanticus_web_users_configuration-0.1.5-py3-none-any.whl',
        'atlanticus/web/users/configuration/web/layout.py',
    )
    users_callbacks = _read(
        'atlanticus_web_users_configuration-0.1.5-py3-none-any.whl',
        'atlanticus/web/users/configuration/web/callbacks.py',
    )
    navigation_layout = _read(
        'atlanticus_web_navigation_configuration-0.1.4-py3-none-any.whl',
        'atlanticus/web/navigation/configuration/web/layout.py',
    )
    navigation_callbacks = _read(
        'atlanticus_web_navigation_configuration-0.1.4-py3-none-any.whl',
        'atlanticus/web/navigation/configuration/web/callbacks.py',
    )

    assert 'Importar configuración de herramienta' in tools_layout
    assert 'Importar archivo de Users' in users_layout
    assert 'Importar archivo de Navigation' in navigation_layout
    for callbacks in (tools_callbacks, users_callbacks, navigation_callbacks):
        assert 'base_source_revision=source_revision' in callbacks
