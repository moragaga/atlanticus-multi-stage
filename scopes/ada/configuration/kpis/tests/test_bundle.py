from datetime import UTC, datetime

from ada.configuration.kpis import KpiBinding, KpiConfiguration
from ada.configuration.kpis.bundle import (
    KpiConfigurationBundle,
    KpiConfigurationSourceDocument,
    build_kpi_configuration_digest,
    decode_kpi_configuration_source,
    encode_kpi_configuration_source,
)


def _configuration(key: str) -> KpiConfiguration:
    return KpiConfiguration((KpiBinding(key=key, destination_keys=('molienda',)),))


def test_bundle_revision_is_content_digest() -> None:
    configuration = _configuration('kpi_a')
    bundle = KpiConfigurationBundle.create(
        configuration=configuration,
        saved_by='tester',
        now_utc=datetime(2026, 8, 24, 20, 0, tzinfo=UTC),
    )

    assert bundle.revision == build_kpi_configuration_digest(configuration)


def test_source_document_preserves_current_and_history() -> None:
    first = KpiConfigurationBundle.create(
        configuration=_configuration('kpi_a'),
        saved_by='first',
        now_utc=datetime(2026, 8, 24, 20, 0, tzinfo=UTC),
    )
    second = KpiConfigurationBundle.create(
        configuration=_configuration('kpi_b'),
        saved_by='second',
        now_utc=datetime(2026, 8, 24, 20, 1, tzinfo=UTC),
    )

    source = KpiConfigurationSourceDocument.from_bundle(first).publish(second)

    assert source.current_bundle() == second
    assert source.fetch_revision(first.revision) == first
    assert source.list_history(limit=2) == (second, first)


def test_source_gzip_roundtrip_is_deterministic() -> None:
    bundle = KpiConfigurationBundle.create(
        configuration=_configuration('kpi_a'),
        saved_by='tester',
        now_utc=datetime(2026, 8, 24, 20, 0, tzinfo=UTC),
    )
    source = KpiConfigurationSourceDocument.from_bundle(bundle)

    payload = encode_kpi_configuration_source(source)

    assert payload == encode_kpi_configuration_source(source)
    assert decode_kpi_configuration_source(payload) == source
