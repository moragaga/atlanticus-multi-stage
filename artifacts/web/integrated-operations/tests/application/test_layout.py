from types import SimpleNamespace

from atlanticus.web.services import ServiceRegistry
from integrated_operations.application.layout import build_application_layout


def test_application_layout_uses_effective_operational_composition(monkeypatch) -> None:
    operational = object()
    application = SimpleNamespace(operational=operational)
    expected = object()
    monkeypatch.setattr(
        'integrated_operations.application.layout.build_integrated_operations_tool',
        lambda value: expected if value is operational else None,
    )

    result = build_application_layout(
        ServiceRegistry(),
        composition=application,
    )

    assert result is expected
