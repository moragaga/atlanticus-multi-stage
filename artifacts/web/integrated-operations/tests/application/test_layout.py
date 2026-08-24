from types import SimpleNamespace

from ada.contracts.tool_manifest import ToolManifestResolution
from atlanticus.web.services import ServiceRegistry
from integrated_operations.application.layout import build_application_layout


def test_application_layout_uses_effective_operational_composition(monkeypatch) -> None:
    composition = SimpleNamespace()
    expected = object()
    monkeypatch.setattr(
        'integrated_operations.application.layout.build_integrated_operations_tool',
        lambda value: expected if value is composition else None,
    )

    result = build_application_layout(
        ServiceRegistry(),
        configuration_resolution=ToolManifestResolution.not_projected(),
        composition=composition,
    )

    assert result is expected
