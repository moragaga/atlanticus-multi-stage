import pytest

from ada.configuration.kpis import KpiBinding, KpiConfiguration
from ada.configuration.kpis.errors import KpiConfigurationValidationError


def test_binding_keeps_legacy_latest_series_semantics_without_tool_or_slots() -> None:
    binding = KpiBinding(
        key='produccion_total',
        destination_keys=('global_indicators', 'molienda'),
        latest_enabled=True,
        series_enabled=True,
        series_hours=24,
    )

    assert binding.key == 'produccion_total'
    assert binding.destination_keys == ('global_indicators', 'molienda')
    assert binding.enabled
    assert binding.latest_enabled
    assert binding.series_enabled
    assert binding.series_hours == 24
    assert 'tool_key' not in binding.to_document()
    assert 'component_key' not in binding.to_document()
    assert 'slot_keys' not in binding.to_document()


def test_binding_can_be_disabled_without_an_extra_enabled_field() -> None:
    binding = KpiBinding(
        key='kpi_desactivado',
        destination_keys=('time_status',),
        latest_enabled=False,
        series_enabled=False,
    )

    assert not binding.enabled
    assert binding.series_hours is None
    assert 'enabled' not in binding.to_document()


def test_binding_requires_one_or_more_unique_destinations() -> None:
    with pytest.raises(KpiConfigurationValidationError, match='at least one destination'):
        KpiBinding(key='kpi', destination_keys=())

    with pytest.raises(KpiConfigurationValidationError, match='must be unique'):
        KpiBinding(key='kpi', destination_keys=('molienda', 'molienda'))


def test_series_hours_is_only_valid_for_enabled_series() -> None:
    with pytest.raises(KpiConfigurationValidationError, match='positive integer'):
        KpiBinding(
            key='kpi',
            destination_keys=('molienda',),
            series_enabled=True,
            series_hours=None,
        )

    with pytest.raises(KpiConfigurationValidationError, match='must be empty'):
        KpiBinding(
            key='kpi',
            destination_keys=('molienda',),
            series_enabled=False,
            series_hours=24,
        )


def test_configuration_supports_immutable_add_replace_remove() -> None:
    first = KpiBinding(key='kpi_a', destination_keys=('molienda',))
    second = KpiBinding(key='kpi_b', destination_keys=('flotacion',))
    configuration = KpiConfiguration().add_binding(first).add_binding(second)

    replacement = KpiBinding(
        key='kpi_a',
        destination_keys=('global_indicators', 'molienda'),
        latest_enabled=False,
        series_enabled=True,
        series_hours=12,
    )
    replaced = configuration.replace_binding(replacement)
    removed = replaced.remove_binding('kpi_b')

    assert replaced.binding('kpi_a') == replacement
    assert removed.bindings == (replacement,)


def test_configuration_roundtrip_preserves_multi_destination_contract() -> None:
    configuration = KpiConfiguration(
        bindings=(
            KpiBinding(
                key='kpi_a',
                destination_keys=('global_indicators', 'molienda'),
                latest_enabled=True,
                series_enabled=True,
                series_hours=48,
            ),
        )
    )

    assert KpiConfiguration.from_document(configuration.to_document()) == configuration
