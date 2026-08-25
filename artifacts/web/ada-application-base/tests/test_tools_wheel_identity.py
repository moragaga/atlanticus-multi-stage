from __future__ import annotations

from importlib.metadata import version
from pathlib import Path
from zipfile import ZipFile

TOOLS_VERSION = '0.1.13'
TOOLS_WHEEL_NAME = f'ada_configuration_tools-{TOOLS_VERSION}-py3-none-any.whl'


def test_installed_tools_distribution_uses_current_version() -> None:
    assert version('ada-configuration-tools') == TOOLS_VERSION


def test_tools_transport_has_unique_current_wheel() -> None:
    artifact = Path(__file__).resolve().parents[1]
    wheels = sorted(artifact.joinpath('wheels').glob('ada_configuration_tools-*.whl'))

    assert [wheel.name for wheel in wheels] == [TOOLS_WHEEL_NAME]


def test_tools_wheel_consumes_initial_manager_draft_without_global_duplicate_policy() -> None:
    artifact = Path(__file__).resolve().parents[1]
    wheel = artifact / 'wheels' / TOOLS_WHEEL_NAME

    with ZipFile(wheel) as archive:
        callbacks = archive.read('ada/configuration/tools/web/callbacks.py').decode('utf-8')

    function_start = callbacks.index('def load_browser_draft(')
    decorator_start = callbacks.rfind('@app.callback(', 0, function_start)
    loader = callbacks[decorator_start:function_start]

    assert "Output(CONFIGURATION_STORE_ID, 'data')" in loader
    assert "Output(SOURCE_REVISION_STORE_ID, 'data')" in loader
    assert 'allow_duplicate=True' not in loader
    assert 'prevent_initial_call' not in loader
    assert "prevent_initial_callbacks='initial_duplicate'" not in callbacks


def test_tools_wheel_exposes_only_single_tool_configuration_ui() -> None:
    artifact = Path(__file__).resolve().parents[1]
    wheel = artifact / 'wheels' / TOOLS_WHEEL_NAME

    with ZipFile(wheel) as archive:
        layout = archive.read('ada/configuration/tools/web/layout.py').decode('utf-8')
        callbacks = archive.read('ada/configuration/tools/web/callbacks.py').decode('utf-8')
        ids = archive.read('ada/configuration/tools/web/ids.py').decode('utf-8')

    combined = '\n'.join((layout, callbacks, ids))
    assert 'Configuración única de herramienta' in layout
    assert 'Configurar herramienta' not in layout
    assert 'Selecciona una herramienta' not in layout
    assert '+ Nueva herramienta' not in layout
    assert 'ToolConfigurationCatalog' not in combined
    assert 'SELECTED_TOOL_ID' not in combined
    assert 'Tool configuration already exists' not in callbacks
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
    assert 'id=ADD_COMPONENT_ID,\n                                disabled=True' in layout
    assert 'id=ADD_SUBCOMPONENT_ID,\n                                disabled=True' in layout
    assert 'def toggle_structure_actions(' in callbacks
    assert "Input(TOOL_KIND_ID, 'value')" in callbacks
    assert 'Tool configuration is required' not in callbacks
