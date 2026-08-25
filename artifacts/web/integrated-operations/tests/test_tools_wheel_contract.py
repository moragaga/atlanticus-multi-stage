from pathlib import Path
from zipfile import ZipFile

TOOLS_WHEEL = 'ada_configuration_tools-0.1.11-py3-none-any.whl'


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
    assert 'Tool configuration already exists' not in callbacks
    assert 'Configurar herramienta' not in layout
    assert 'CREATE_' not in combined
    assert '_tool_modal' not in layout
    assert 'ada-tools-create-' not in combined
    assert "data.get('schema_version') not in {1, 2}" in callbacks
    assert "'schema_version': 1" in callbacks
    assert 'Configuración sensible' in layout
    assert 'id=TOOL_KEY_ID' in layout
    assert 'id=TOOL_KIND_ID' in layout
    assert 'Cambio de alto impacto' in callbacks
    assert "State(TOOL_KIND_ID, 'value')" in callbacks
    assert 'Tool configuration is required' not in callbacks
