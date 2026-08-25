from pathlib import Path


def _callbacks() -> str:
    return (Path(__file__).parents[1] / 'src/ada/configuration/tools/web/callbacks.py').read_text(
        encoding='utf-8'
    )


def test_tool_editor_keeps_structural_identity_editable_with_explicit_risk_guidance() -> None:
    root = Path(__file__).parents[1] / 'src/ada/configuration/tools/web'
    layout = (root / 'layout.py').read_text(encoding='utf-8')
    callbacks = _callbacks()

    assert 'dash_table' not in layout
    assert 'Importar configuración de herramienta' in layout
    assert "'label': 'Mina y Planta'" in layout
    assert 'CREATE_MODAL_ID' not in layout
    assert 'COMPONENT_MODAL_ID' in layout
    assert 'SUBCOMPONENT_MODAL_ID' in layout
    assert 'id=ADD_COMPONENT_ID,\n                                disabled=True' in layout
    assert 'id=ADD_SUBCOMPONENT_ID,\n                                disabled=True' in layout
    assert 'Configuración sensible' in layout
    assert 'Define cuidadosamente el identificador, el tipo y el área' in layout
    assert 'id=TOOL_KEY_ID' in layout
    assert 'id=TOOL_KIND_ID' in layout
    assert "_reference_field(\n                        'Aplicación'" in layout
    assert "Output(TOOL_KEY_ID, 'value')" in callbacks
    assert "Output(TOOL_KIND_ID, 'value')" in callbacks
    assert 'render_application_key' in callbacks
    assert "{'label': 'Mina y Planta', 'value': 'global', 'disabled': True}" in layout
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
    assert "Output(SOURCE_REVISION_STORE_ID, 'data')" in callbacks


def test_tool_source_draft_consumer_owns_initial_store_hydration() -> None:
    callbacks = _callbacks()
    start = callbacks.index('@app.callback(', callbacks.index('def register_tool_admin_callbacks('))
    end = callbacks.index('def load_browser_draft(')
    decorator = callbacks[start:end]

    assert "Output(CONFIGURATION_STORE_ID, 'data')" in decorator
    assert "Output(DRAFT_LOAD_SIGNAL_ID, 'data')" in decorator
    assert "Output(SOURCE_REVISION_STORE_ID, 'data')" in decorator
    assert "Output(SOURCE_CONFIGURATION_STORE_ID, 'data')" in decorator
    assert 'allow_duplicate=True' not in decorator
    assert 'prevent_initial_call' not in decorator


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
    assert 'Configurar herramienta' not in layout
    assert '_tool_modal' not in layout
    assert 'CREATE_' not in layout
    assert 'CREATE_' not in callbacks
    assert 'CREATE_' not in ids
    assert 'Tool configuration already exists' not in callbacks
    assert 'ToolManifestRegistry' not in callbacks


def test_initial_configuration_is_created_by_saving_the_inline_editor() -> None:
    root = Path(__file__).parents[1] / 'src/ada/configuration/tools/web'
    layout = (root / 'layout.py').read_text(encoding='utf-8')
    callbacks = _callbacks()
    function_start = callbacks.index('def save_tool_draft(')
    start = callbacks.rfind('@app.callback(', 0, function_start)
    end = callbacks.index('def _raw_editor_revision(')
    callback = callbacks[start:end]

    assert "'Guardar borrador'" in layout
    assert '_build_tool_from_editor(' in callback
    assert "State(CONFIGURATION_STORE_ID, 'data')" not in callback
    assert '_require_configuration(' not in callbacks
    assert 'CREATE_' not in callbacks


def test_published_source_identity_is_kept_in_memory_for_structural_change_detection() -> None:
    root = Path(__file__).parents[1] / 'src/ada/configuration/tools/web'
    layout = (root / 'layout.py').read_text(encoding='utf-8')
    callbacks = _callbacks()

    assert 'SOURCE_CONFIGURATION_STORE_ID' in layout
    assert "storage_type='memory'" in layout
    assert '_browser_draft_matches_source(' in callbacks
    assert '_structural_change_labels(' in callbacks
    assert 'context.services.administration.load_source()' not in callbacks


def test_structural_change_warning_is_advisory_and_does_not_block_draft_save() -> None:
    root = Path(__file__).parents[1] / 'src/ada/configuration/tools/web'
    layout = (root / 'layout.py').read_text(encoding='utf-8')
    callbacks = _callbacks()

    assert 'Cambio de alto impacto' in callbacks
    assert 'Revisa y actualiza las configuraciones dependientes antes' in callbacks
    assert "Output(STRUCTURAL_CHANGE_WARNING_ID, 'children')" in callbacks
    assert "State(TOOL_KEY_ID, 'value')" in callbacks
    assert "State(TOOL_KIND_ID, 'value')" in callbacks
    assert (
        'disabled=True'
        not in layout[layout.index('Identificador') : layout.index('Fuentes y freshness')]
    )


def test_structure_editor_uses_inline_tool_kind_and_modal_close_does_not_require_saved_tool() -> (
    None
):
    callbacks = _callbacks()

    render_start = callbacks.index('def render_structure(')
    render_block = callbacks[
        callbacks.rfind('@app.callback(', 0, render_start) : callbacks.index(
            'def component_editor('
        )
    ]
    component_start = callbacks.index('def component_editor(')
    component_block = callbacks[
        callbacks.rfind('@app.callback(', 0, component_start) : callbacks.index(
            'def delete_component('
        )
    ]
    subcomponent_start = callbacks.index('def subcomponent_editor(')
    subcomponent_block = callbacks[
        callbacks.rfind('@app.callback(', 0, subcomponent_start) : callbacks.index(
            'def linked_component_options('
        )
    ]
    linked_start = callbacks.index('def linked_component_options(')
    linked_block = callbacks[
        callbacks.rfind('@app.callback(', 0, linked_start) : callbacks.index(
            'def delete_subcomponent('
        )
    ]

    assert "Input(TOOL_KIND_ID, 'value')" in render_block
    assert "State(CONFIGURATION_STORE_ID, 'data')" not in render_block
    assert "State(TOOL_KIND_ID, 'value')" in component_block
    assert "State(CONFIGURATION_STORE_ID, 'data')" not in component_block
    assert 'Tool configuration is required' not in component_block
    assert component_block.index('if _matches_trigger(') < component_block.index(
        'kind = _optional_tool_kind(kind_value)'
    )
    assert "State(TOOL_KIND_ID, 'value')" in subcomponent_block
    assert "State(CONFIGURATION_STORE_ID, 'data')" not in subcomponent_block
    assert 'Tool configuration is required' not in subcomponent_block
    assert subcomponent_block.index('if _matches_trigger(') < subcomponent_block.index(
        'kind = _optional_tool_kind(kind_value)'
    )
    assert "State(TOOL_KIND_ID, 'value')" in linked_block
    assert "State(CONFIGURATION_STORE_ID, 'data')" not in linked_block
    assert 'def _save_component_draft(\n    *,\n    kind: ToolConfigurationKind,' in callbacks
    assert 'def _save_subcomponent_draft(\n    *,\n    kind: ToolConfigurationKind,' in callbacks
    assert 'def _validate_linked_components(\n    kind: ToolConfigurationKind,' in callbacks


def test_structure_actions_require_tool_kind_and_parent_component() -> None:
    callbacks = _callbacks()
    start = callbacks.rindex('@app.callback(', 0, callbacks.index('def toggle_structure_actions('))
    end = callbacks.index('def toggle_source_fields(', start)
    callback = callbacks[start:end]

    assert "Output(ADD_COMPONENT_ID, 'disabled')" in callback
    assert "Output(ADD_SUBCOMPONENT_ID, 'disabled')" in callback
    assert "Input(TOOL_KIND_ID, 'value')" in callback
    assert "Input(STRUCTURE_STORE_ID, 'data')" in callback
    assert 'has_kind = _optional_tool_kind(kind_value) is not None' in callback
    assert 'has_components = bool(_structure_components(structure_data))' in callback
    assert 'return not has_kind, not (has_kind and has_components)' in callback
