import pytest

from ada.ui.components.global_indicator import (
    GlobalIndicatorDefinition,
    GlobalIndicatorDefinitionError,
    GlobalIndicatorMeasurementDefinition,
)


def test_definition_preserves_kpi_key_contract() -> None:
    definition = GlobalIndicatorMeasurementDefinition.temporal('Día')

    assert definition.temporality_key == 'dia'
    assert definition.real_kpi_key(default_key='recuperacion_cu') == 'recuperacion_cu_dia_real_inst'
    assert definition.plan_kpi_key(default_key='recuperacion_cu') == 'recuperacion_cu_dia_plan_inst'
    assert (
        definition.color_kpi_key(default_key='recuperacion_cu') == 'recuperacion_cu_dia_color_inst'
    )


def test_definition_allows_day_week_and_one_last_measurement() -> None:
    definition = GlobalIndicatorDefinition(
        key='recuperacion_cu',
        label='Recuperación Cu',
        unit='%',
        measurements=(
            GlobalIndicatorMeasurementDefinition.temporal('Día'),
            GlobalIndicatorMeasurementDefinition.temporal('Semana'),
            GlobalIndicatorMeasurementDefinition.last_measurement(),
        ),
    )

    assert len(definition.measurements) == 3
    assert definition.measurements[-1].is_last_measurement is True


def test_definition_rejects_multiple_last_measurements() -> None:
    with pytest.raises(GlobalIndicatorDefinitionError, match='at most one last measurement'):
        GlobalIndicatorDefinition(
            key='recuperacion_cu',
            label='Recuperación Cu',
            unit='%',
            measurements=(
                GlobalIndicatorMeasurementDefinition.last_measurement(source_key='a'),
                GlobalIndicatorMeasurementDefinition.last_measurement('latest', source_key='b'),
            ),
        )
