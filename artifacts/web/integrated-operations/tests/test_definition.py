from integrated_operations.definition import (
    build_dashboard_configuration,
    build_manifest,
    build_renderer_registry,
)


def test_definition_uses_real_integrated_operations_contract() -> None:
    manifest = build_manifest()
    configuration = build_dashboard_configuration()
    renderers = build_renderer_registry()

    assert manifest.tool_key == 'integrated_operations'
    assert len(configuration.components) == 9
    assert len(renderers.definitions) == 9
    assert configuration.time_series is not None
    assert configuration.time_series.step_seconds == 60
