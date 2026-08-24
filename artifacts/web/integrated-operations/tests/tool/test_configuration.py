from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from integrated_operations.tool.configuration import (
    build_dashboard_configuration,
    build_renderer_registry,
)


def test_configuration_uses_supplied_integrated_operations_manifest() -> None:
    configuration = build_dashboard_configuration(INTEGRATED_OPERATIONS_MANIFEST)
    renderers = build_renderer_registry(INTEGRATED_OPERATIONS_MANIFEST)

    assert len(configuration.components) == 9
    assert len(renderers.definitions) == 9
    assert configuration.time_series is not None
    assert configuration.time_series.step_seconds == 60
