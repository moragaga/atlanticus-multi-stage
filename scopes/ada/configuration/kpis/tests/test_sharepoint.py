import base64
from datetime import UTC, datetime

from ada.configuration.kpis import KpiBinding, KpiConfiguration
from ada.configuration.kpis.adapters.sharepoint import (
    SharePointKpiConfigurationSettings,
    SharePointKpiConfigurationStore,
)
from ada.configuration.kpis.bundle import KpiConfigurationBundle


class Gateway:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def read(self, *, filename: str, relative_path: str) -> str | None:
        return self.values.get((relative_path, filename))

    def write(self, *, filename: str, relative_path: str, content: str) -> None:
        self.values[(relative_path, filename)] = content


def test_sharepoint_source_uses_separate_kpi_path_and_history() -> None:
    gateway = Gateway()
    store = SharePointKpiConfigurationStore(
        gateway=gateway,
        settings=SharePointKpiConfigurationSettings(),
    )
    first = KpiConfigurationBundle.create(
        configuration=KpiConfiguration((KpiBinding(key='kpi_a', destination_keys=('molienda',)),)),
        saved_by='first',
        now_utc=datetime(2026, 8, 24, 20, 0, tzinfo=UTC),
    )
    second = KpiConfigurationBundle.create(
        configuration=KpiConfiguration(
            (KpiBinding(key='kpi_b', destination_keys=('time_status',)),)
        ),
        saved_by='second',
        now_utc=datetime(2026, 8, 24, 20, 1, tzinfo=UTC),
    )

    store.publish_bundle(first, expected_source_revision=None)
    store.publish_bundle(second, expected_source_revision=first.revision)

    content = gateway.values[('kpis', 'kpi_configuration.json.gz')]
    assert base64.b64decode(content, validate=True)[:2] == b'\x1f\x8b'
    assert store.fetch_bundle() == second
    assert store.list_history(limit=2) == (second, first)
