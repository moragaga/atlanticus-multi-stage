from types import SimpleNamespace

from ada.contracts.tool_manifest import ToolManifestResolution
from atlanticus.web.services import ServiceRegistry
from integrated_operations.application.layout import build_application_layout


def _text(component) -> str:
    return str(component.to_plotly_json())


def test_not_projected_layout_reports_configuration_is_not_available() -> None:
    layout = build_application_layout(
        ServiceRegistry(),
        resolution=ToolManifestResolution.not_projected(),
        composition=None,
    )

    assert 'projected configuration for this tool is not available yet' in _text(layout)


def test_ready_layout_uses_projected_composition(monkeypatch) -> None:
    composition = SimpleNamespace()
    expected = object()
    monkeypatch.setattr(
        'integrated_operations.application.layout.build_integrated_operations_tool',
        lambda value: expected if value is composition else None,
    )

    result = build_application_layout(
        ServiceRegistry(),
        resolution=ToolManifestResolution.not_projected(),
        composition=composition,
    )

    assert result is expected
