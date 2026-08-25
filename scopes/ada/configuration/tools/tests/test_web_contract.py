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
    assert 'Importar configuración de herramienta' in layout
    assert "'label': 'Mina y Planta'" in layout
    assert 'CREATE_MODAL_ID' in layout
    assert 'COMPONENT_MODAL_ID' in layout
    assert 'SUBCOMPONENT_MODAL_ID' in layout
    assert 'El identificador estable se genera automáticamente.' in layout
    assert 'if kind is ToolConfigurationKind.INTEGRATED_OPERATIONS' in callbacks
    assert 'else build_identity_key(name)' in callbacks
    assert "if 'pi' in selected:" in callbacks
    assert "if 'dispatch' in selected:" in callbacks


def test_import_loads_configuration_into_browser_draft_without_publishing_source() -> None:
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
    assert 'publish_configuration' not in callback
    assert 'save_configuration' not in callback
    assert "endswith('.json.gz')" not in callback


def test_save_draft_updates_workspace_and_persistent_checkpoint_without_source_write() -> None:
    callbacks = _callbacks()
    function_start = callbacks.index('def save_tool_draft(')
    start = callbacks.rfind('@app.callback(', 0, function_start)
    end = callbacks.index('def _configuration_from_browser_draft(')
    callback = callbacks[start:end]

    assert 'Output(context.draft_store_id' in callbacks
    assert 'Output(context.saved_draft_store_id' in callback
    assert '_browser_draft_document(' in callback
    assert 'publish_configuration' not in callback
    assert 'save_configuration' not in callback
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


def test_structure_is_reloaded_from_browser_draft_not_source_refresh() -> None:
    callbacks = _callbacks()
    before_structure = callbacks.split('def load_tool_structure(', 1)[0]
    load_structure = before_structure.rsplit('@app.callback(', 1)[1]

    assert "Output(STRUCTURE_STORE_ID, 'data')" in load_structure
    assert "Input(CONFIGURATION_STORE_ID, 'data')" in load_structure
    assert "Input(DRAFT_LOAD_SIGNAL_ID, 'data')" in load_structure
    assert "Input(SOURCE_REVISION_STORE_ID, 'data')" not in load_structure


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


def test_tool_workspace_starts_empty_and_does_not_read_source_implicitly() -> None:
    root = Path(__file__).parents[1] / 'src/ada/configuration/tools/web'
    layout = (root / 'layout.py').read_text(encoding='utf-8')
    callbacks = _callbacks()

    assert 'context.services.administration.load_source()' not in layout
    assert 'dcc.Store(id=CONFIGURATION_STORE_ID, data=None' in layout
    assert 'data=None' in layout
    assert 'def refresh_source_revision(' not in callbacks
    assert (
        'if draft_data is None:'
        in callbacks[
            callbacks.index('def load_browser_draft(') : callbacks.index(
                'def track_editor_revision('
            )
        ]
    )
    tracker = callbacks[
        callbacks.index("Output(context.editor_revision_store_id, 'data')") : callbacks.index(
            'def track_editor_revision('
        )
    ]
    assert 'prevent_initial_call=True' in tracker


def test_tool_browser_draft_wrapper_matches_manager_draft_schema() -> None:
    callbacks = _callbacks()

    assert "data.get('schema_version') not in {1, 2}" in callbacks
    browser_writer = callbacks[
        callbacks.index('def _browser_draft_document(') : callbacks.index(
            'def _draft_base_source_revision('
        )
    ]
    assert "'schema_version': 1" in browser_writer
    assert "'schema_version': 2" not in browser_writer


def test_tool_editor_exposes_one_configuration_without_tool_selector_or_catalog() -> None:
    root = Path(__file__).parents[1] / 'src/ada/configuration/tools/web'
    layout = (root / 'layout.py').read_text(encoding='utf-8')
    callbacks = _callbacks()
    ids = (root / 'ids.py').read_text(encoding='utf-8')

    assert 'SELECTED_TOOL_ID' not in layout
    assert 'SELECTED_TOOL_ID' not in callbacks
    assert 'SELECTED_TOOL_ID' not in ids
    assert 'ToolConfigurationCatalog' not in layout
    assert 'ToolConfigurationCatalog' not in callbacks
    assert '+ Nueva herramienta' not in layout
    assert 'Configuración única de herramienta' in layout
    assert 'Tool configuration already exists' in callbacks
    assert 'ToolManifestRegistry' not in callbacks
