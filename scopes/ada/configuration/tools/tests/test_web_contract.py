from pathlib import Path


def _callbacks() -> str:
    return (Path(__file__).parents[1] / 'src/ada/configuration/tools/web/callbacks.py').read_text(
        encoding='utf-8'
    )


def test_tool_editor_uses_controlled_structure_forms_and_reference_only_ids() -> None:
    root = Path(__file__).parents[1] / 'src/ada/configuration/tools/web'
    layout = (root / 'layout.py').read_text(encoding='utf-8')
    callbacks = _callbacks()

    assert 'dash_table' not in layout
    assert 'Cargar archivo de configuración local' in layout
    assert "'label': 'Mina y Planta'" in layout
    assert 'CREATE_MODAL_ID' in layout
    assert 'COMPONENT_MODAL_ID' in layout
    assert 'SUBCOMPONENT_MODAL_ID' in layout
    assert 'El identificador estable se genera automáticamente.' in layout
    assert 'build_identity_key(name)' in callbacks
    assert "if 'pi' in selected:" in callbacks
    assert "if 'dispatch' in selected:" in callbacks


def test_import_loads_catalog_into_browser_draft_without_publishing_source() -> None:
    root = Path(__file__).parents[1] / 'src/ada/configuration/tools/web'
    layout = (root / 'layout.py').read_text(encoding='utf-8')
    callbacks = _callbacks()
    start = callbacks.index('def import_configuration(')
    end = callbacks.index('def save_tool_draft(')
    callback = callbacks[start:end]

    assert 'Importar .json.gz' not in layout
    assert 'if contents is None:' in callback
    assert 'decode_tool_configuration_import(payload)' in callback
    assert '_browser_draft_document(' in callback
    assert 'publish_catalog' not in callback
    assert 'save_catalog' not in callback
    assert "endswith('.json.gz')" not in callback


def test_save_draft_targets_browser_local_store_not_source_store() -> None:
    callbacks = _callbacks()
    start = callbacks.index('def save_tool_draft(')
    end = callbacks.index('def _catalog_from_browser_draft(')
    callback = callbacks[start:end]

    assert 'Output(context.draft_store_id' in callbacks
    assert '_browser_draft_document(' in callback
    assert 'publish_catalog' not in callback
    assert 'save_catalog' not in callback
    assert "_success('Borrador guardado en este navegador.')" not in callback


def test_source_freshness_controls_are_hidden_when_source_is_not_selected() -> None:
    root = Path(__file__).parents[1]
    callbacks = _callbacks()
    css = (root / 'src/ada/configuration/tools/resources/css/00_tools_admin.css').read_text(
        encoding='utf-8'
    )

    assert 'toggle_source_fields' in callbacks
    assert '_SOURCE_HIDDEN' in callbacks
    assert '.ada-tools-admin__source-field--hidden' in css


def test_structure_is_reloaded_from_selected_browser_draft_not_source_refresh() -> None:
    callbacks = _callbacks()
    before_structure = callbacks.split('def load_tool_structure(', 1)[0]
    load_structure = before_structure.rsplit('@app.callback(', 1)[1]

    assert "Output(STRUCTURE_STORE_ID, 'data')" in load_structure
    assert "Input(SELECTED_TOOL_ID, 'value')" in load_structure
    assert "Input(DRAFT_LOAD_SIGNAL_ID, 'data')" in load_structure
    assert "Input(SOURCE_REVISION_STORE_ID, 'data')" not in load_structure
    assert "State(CATALOG_STORE_ID, 'data')" in load_structure


def test_dynamic_structure_actions_require_a_real_pattern_button_click() -> None:
    callbacks = _callbacks()

    assert 'def _pattern_click_is_real(' in callbacks
    assert "State(component_edit_id(ALL), 'id')" in callbacks
    assert "State(component_delete_id(ALL), 'id')" in callbacks
    assert "State(component_move_id(ALL, ALL), 'id')" in callbacks
    assert "State(subcomponent_edit_id(ALL, ALL), 'id')" in callbacks
    assert "State(subcomponent_delete_id(ALL, ALL), 'id')" in callbacks
    assert "State(subcomponent_move_id(ALL, ALL, ALL), 'id')" in callbacks
    assert callbacks.count('not _pattern_click_is_real(') >= 6
    assert callbacks.count('n_clicks=0') >= 8


def test_editor_success_messages_do_not_accumulate_after_structure_changes() -> None:
    callbacks = _callbacks()

    assert "_success('Componente actualizado en el borrador.')" not in callbacks
    assert "_success('Componente eliminado del borrador.')" not in callbacks
    assert "_success('Subcomponente actualizado en el borrador.')" not in callbacks
    assert "_success('Subcomponente eliminado del borrador.')" not in callbacks


def test_tool_editor_tracks_the_revision_of_the_content_that_save_draft_would_persist() -> None:
    callbacks = _callbacks()

    assert "Output(context.editor_revision_store_id, 'data')" in callbacks
    assert 'def track_editor_revision(' in callbacks
    assert 'build_tool_configuration_digest(updated)' in callbacks
    assert '_raw_editor_revision(' in callbacks
    assert "Output(SOURCE_REVISION_STORE_ID, 'data', allow_duplicate=True)" in callbacks
