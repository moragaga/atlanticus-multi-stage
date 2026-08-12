import pytest

from ada.ui.components.global_indicator import (
    GlobalIndicatorDefinition,
    GlobalIndicatorDefinitionError,
    IndicatorDefinition,
    IndicatorPropertiesDefinition,
)

_PROPERTIES = IndicatorPropertiesDefinition(
    label='font-size-gi-300',
    temporality='font-size-gi-200',
    real_value='font-size-gi-100',
    plan_value='font-size-gi-200',
    last_measurement_label='font-size-gi-400',
    last_measurement_value='font-size-gi-300',
)


def test_definition_preserves_kpi_key_contract() -> None:
    definition = IndicatorDefinition(temporality='Día', indicator_key='recuperacion_cu')

    assert definition.temporality_key == 'dia'
    assert definition.real_kpi_key == 'recuperacion_cu_dia_real_inst'
    assert definition.plan_kpi_key == 'recuperacion_cu_dia_plan_inst'
    assert definition.color_kpi_key == 'recuperacion_cu_dia_color_inst'


def test_definition_allows_day_week_and_one_last_measurement() -> None:
    definition = GlobalIndicatorDefinition(
        label='Recuperación Cu',
        unit='%',
        properties=_PROPERTIES,
        indicators=(
            IndicatorDefinition('Día', 'recuperacion_cu'),
            IndicatorDefinition('Semana', 'recuperacion_cu'),
            IndicatorDefinition('actual', 'recuperacion_cu', only_last_measurement=True),
        ),
    )

    assert len(definition.indicators) == 3
    assert definition.indicators[-1].only_last_measurement is True


def test_definition_rejects_multiple_last_measurements() -> None:
    with pytest.raises(GlobalIndicatorDefinitionError, match='at most one last measurement'):
        GlobalIndicatorDefinition(
            label='Recuperación Cu',
            unit='%',
            properties=_PROPERTIES,
            indicators=(
                IndicatorDefinition('actual', 'a', only_last_measurement=True),
                IndicatorDefinition('latest', 'b', only_last_measurement=True),
            ),
        )
