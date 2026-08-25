from pathlib import Path


def _web_source(filename: str) -> str:
    return (Path(__file__).parents[1] / 'src/ada/configuration/kpis/web' / filename).read_text(
        encoding='utf-8'
    )


def test_kpi_manager_requires_stable_tool_projection_without_fallbacks() -> None:
    callbacks = _web_source('callbacks.py')
    layout = _web_source('layout.py')

    assert 'context.services.destinations.load()' in callbacks
    assert 'Tool Projection administrativa disponible' in callbacks
    assert 'Tool projection is not available' in callbacks
    assert 'Primero configura y proyecta una herramienta ADA' in layout
    assert 'Ir a Herramientas' in layout
    assert 'baseline operacional como fallback' in layout
    assert 'administration.load_source' not in callbacks
    assert 'list_history' not in callbacks
    assert 'ToolConfiguration' not in callbacks


def test_kpi_editor_uses_only_new_binding_contract() -> None:
    callbacks = _web_source('callbacks.py')
    layout = _web_source('layout.py')

    assert 'destination_keys=' in callbacks
    assert 'latest_enabled=' in callbacks
    assert 'series_enabled=' in callbacks
    assert 'series_hours=' in callbacks
    assert 'multi=True' in layout
    assert "'Latest'" in layout
    assert "'Series'" in layout
    assert 'Horas de serie' in layout

    legacy_terms = (
        'tool_key',
        'KpiToolDefinition',
        'KpiComponentDefinition',
        'slot_keys',
        'layout_type',
        'include_snapshot',
        'timeseries_hours',
    )
    product = callbacks + layout
    for term in legacy_terms:
        assert term not in product


def test_kpi_editor_does_not_hardcode_application_or_destination_names() -> None:
    product = _web_source('callbacks.py') + _web_source('layout.py')

    for term in (
        'integrated_operations',
        'process',
        'molienda',
        'puerto',
        'global_indicators_mine',
        'global_indicators_plant',
    ):
        assert term not in product.lower()


def test_missing_projected_destinations_are_visible_but_not_silently_reconciled() -> None:
    callbacks = _web_source('callbacks.py')

    assert "f'{key} · no disponible en Tool Projection'" in callbacks
    assert "'disabled': True" in callbacks
    assert "destination_names.get(key, f'{key} · no disponible')" in callbacks
    start = callbacks.index('def render_destination_options(')
    end = callbacks.index('def toggle_series_hours(')
    assert '.remove_binding(' not in callbacks[start:end]


def test_kpi_source_draft_consumer_owns_initial_store_hydration() -> None:
    callbacks = _web_source('callbacks.py')
    start = callbacks.index('@app.callback(', callbacks.index('def register_kpi_admin_callbacks('))
    end = callbacks.index('def load_browser_draft(')
    decorator = callbacks[start:end]

    assert "Output(CONFIGURATION_STORE_ID, 'data')" in decorator
    assert "Output(SOURCE_REVISION_STORE_ID, 'data')" in decorator
    assert 'allow_duplicate=True' not in decorator
    assert 'prevent_initial_call' not in decorator


def test_kpi_draft_uses_manager_local_workspace_and_not_source_publication() -> None:
    callbacks = _web_source('callbacks.py')
    function_start = callbacks.index('def save_kpi_draft(')
    start = callbacks.rfind('@app.callback(', 0, function_start)
    end = callbacks.index('def _configuration(')
    callback = callbacks[start:end]

    assert 'Output(context.draft_store_id' in callbacks
    assert 'Output(context.saved_draft_store_id' in callback
    assert '_browser_draft_document(' in callback
    assert 'context.services.destinations.load()' in callback
    assert 'publish_configuration' not in callback
    assert 'projection_workflow.project' not in callback


def test_editing_locks_kpi_identity_and_both_channels_can_be_disabled() -> None:
    callbacks = _web_source('callbacks.py')

    assert "{'mode': 'edit', 'key': binding.key}" in callbacks
    assert 'binding.key,\n                True,' in callbacks
    assert "latest_enabled='enabled' in (latest_values or [])" in callbacks
    assert 'series_enabled=series_enabled' in callbacks
    assert 'series_hours=_series_hours(series_hours) if series_enabled else None' in callbacks
    assert 'or latest_enabled' not in callbacks
