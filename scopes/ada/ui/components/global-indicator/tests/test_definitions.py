import pytest

from ada.ui.components.global_indicator import (
    GlobalIndicatorDefinition,
    GlobalIndicatorDefinitionError,
    GlobalIndicatorLastMeasurementDefinition,
    GlobalIndicatorMeasurementDefinition,
)


def _measurement(key: str, label: str) -> GlobalIndicatorMeasurementDefinition:
    return GlobalIndicatorMeasurementDefinition(key=key, label=label)


def test_definition_generates_runtime_kpi_keys_from_measurement_key() -> None:
    definition = _measurement('dia', 'Día')

    assert definition.actual_kpi_key(default_key='recuperacion_cu') == (
        'recuperacion_cu_dia_real_inst'
    )
    assert definition.plan_kpi_key(default_key='recuperacion_cu') == (
        'recuperacion_cu_dia_plan_inst'
    )
    assert definition.color_kpi_key(default_key='recuperacion_cu') == (
        'recuperacion_cu_dia_color_inst'
    )


def test_definition_exposes_complete_measurement_and_runtime_key_catalog() -> None:
    definition = GlobalIndicatorDefinition(
        key='recuperacion_cu',
        label='Recuperación Cu',
        unit='%',
        measurements=(
            _measurement('turno', 'Turno'),
            _measurement('dia', 'Día'),
            _measurement('semana', 'Semana'),
        ),
        last_measurement=GlobalIndicatorLastMeasurementDefinition(),
    )

    assert definition.measurement_keys == ('turno', 'dia', 'semana')
    assert definition.all_measurement_keys == ('turno', 'dia', 'semana', 'latest')
    assert definition.runtime_kpi_keys() == (
        'recuperacion_cu_turno_real_inst',
        'recuperacion_cu_turno_plan_inst',
        'recuperacion_cu_turno_color_inst',
        'recuperacion_cu_dia_real_inst',
        'recuperacion_cu_dia_plan_inst',
        'recuperacion_cu_dia_color_inst',
        'recuperacion_cu_semana_real_inst',
        'recuperacion_cu_semana_plan_inst',
        'recuperacion_cu_semana_color_inst',
        'recuperacion_cu_latest_real_inst',
        'recuperacion_cu_latest_color_inst',
    )


def test_definition_allows_two_measurements_without_last_measurement() -> None:
    definition = GlobalIndicatorDefinition(
        key='recuperacion_cu',
        label='Recuperación Cu',
        unit='%',
        measurements=(
            _measurement('dia', 'Día'),
            _measurement('semana', 'Semana'),
        ),
    )

    assert definition.measurement_keys == ('dia', 'semana')
    assert definition.last_measurement is None


def test_definition_rejects_more_than_three_measurements() -> None:
    with pytest.raises(
        GlobalIndicatorDefinitionError, match='two or three measurement definitions'
    ):
        GlobalIndicatorDefinition(
            key='recuperacion_cu',
            label='Recuperación Cu',
            unit='%',
            measurements=(
                _measurement('turno', 'Turno'),
                _measurement('dia', 'Día'),
                _measurement('semana', 'Semana'),
                _measurement('mes', 'Mes'),
            ),
        )
