from types import SimpleNamespace

from atlanticus.web.services import ServiceRegistry
from integrated_operations.application.layout import build_application_layout


def test_application_layout_delegates_to_unified_presentation(monkeypatch) -> None:
    application = SimpleNamespace()
    services = ServiceRegistry()
    expected = object()
    captured = {}

    def build_layout(value, *, composition):
        captured['services'] = value
        captured['composition'] = composition
        return expected

    monkeypatch.setattr(
        'integrated_operations.application.layout.build_unified_application_layout',
        build_layout,
    )

    result = build_application_layout(services, composition=application)

    assert result is expected
    assert captured == {'services': services, 'composition': application}
