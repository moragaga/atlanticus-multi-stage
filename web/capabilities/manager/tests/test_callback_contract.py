from pathlib import Path


def _source() -> str:
    return (Path(__file__).parents[1] / 'src/atlanticus/web/manager/web/callbacks.py').read_text(
        encoding='utf-8'
    )


def test_workflow_callbacks_keep_match_scoped_outputs_per_module() -> None:
    source = _source()

    assert 'Output(REFRESH_SIGNAL_ID' not in source
    assert source.count("Input(REFRESH_SIGNAL_ID, 'data')") == 2
    assert source.count("Output(workflow_refresh_signal_id(MATCH), 'data'") == 2
    assert "Input(workflow_refresh_signal_id(ALL), 'data')" in source


def test_workflow_refresh_does_not_rebuild_module_content() -> None:
    source = _source()
    start = source.index("Output(CONTENT_ID, 'children')")
    end = source.index("Output(module_section_store_id(MATCH), 'data')")
    route_callback = source[start:end]

    assert "Input(LOCATION_ID, 'pathname')" in route_callback
    assert "Input(STATUS_STORE_ID, 'data')" not in route_callback
    assert "Output(workflow_status_id(ALL), 'children')" in source
    assert "Output(workflow_action_id(ALL, 'project'), 'disabled')" in source


def test_lifecycle_actions_require_explicit_clicks_and_history_only_loads_draft() -> None:
    source = _source()

    assert 'def validate_configuration(' in source
    assert 'def publish_configuration(' in source
    assert 'def project_configuration(' in source
    assert 'def load_history_as_draft(' in source
    assert 'restore_revision' not in source
    assert "State(history_load_id(MATCH, ALL, ALL), 'id')" in source
    assert 'not _pattern_click_is_real(trigger, clicks, load_ids)' in source
    assert source.count('not _click_is_real(clicks)') >= 3
    assert 'ManagerDraft.create(' in source


def test_validation_does_not_refresh_source_but_publish_and_projection_do() -> None:
    source = _source()
    validate_start = source.rindex('@app.callback(', 0, source.index('def validate_configuration('))
    publish_start = source.rindex('@app.callback(', 0, source.index('def publish_configuration('))
    history_start = source.rindex('@app.callback(', 0, source.index('def load_history_as_draft('))
    validate = source[validate_start:publish_start]
    publish = source[publish_start:history_start]

    assert 'workflow_refresh_signal_id' not in validate
    assert 'workflow_refresh_signal_id' in publish


def test_successful_workflow_actions_use_state_instead_of_persistent_success_banners() -> None:
    source = _source()

    assert 'return None, validation' in source
    assert 'render_validation_result' not in source
    assert 'render_publication_result' not in source
    assert 'render_projection_result' not in source
    assert 'def clear_transient_validation(' in source
    assert "Output(workflow_validation_id(ALL), 'data', allow_duplicate=True)" in source
