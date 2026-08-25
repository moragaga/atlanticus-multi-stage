from pathlib import Path
from zipfile import ZipFile

TOOLS_WHEEL = 'ada_configuration_tools-0.1.8-py3-none-any.whl'


def test_integrated_operations_transports_single_tool_configuration_ui() -> None:
    artifact = Path(__file__).resolve().parents[1]
    wheel = artifact / 'wheels' / TOOLS_WHEEL

    with ZipFile(wheel) as archive:
        layout = archive.read('ada/configuration/tools/web/layout.py').decode('utf-8')
        callbacks = archive.read('ada/configuration/tools/web/callbacks.py').decode('utf-8')
        ids = archive.read('ada/configuration/tools/web/ids.py').decode('utf-8')

    combined = '\n'.join((layout, callbacks, ids))
    assert 'Configuración única de herramienta' in layout
    assert 'Selecciona una herramienta' not in layout
    assert '+ Nueva herramienta' not in layout
    assert 'ToolConfigurationCatalog' not in combined
    assert 'SELECTED_TOOL_ID' not in combined
    assert 'Tool configuration already exists' in callbacks
    assert "data.get('schema_version') not in {1, 2}" in callbacks
    assert "'schema_version': 1" in callbacks
