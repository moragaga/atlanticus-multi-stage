from ada.ui.components.global_indicator import (
    GlobalIndicatorDefinition,
    IndicatorDefinition,
    IndicatorPropertiesDefinition,
    map_global_indicator_data,
)


def test_mapper_supports_last_measurement_without_special_tool_logic() -> None:
    definition = GlobalIndicatorDefinition(
        label='Recuperación Cu',
        unit='%',
        properties=IndicatorPropertiesDefinition(
            label='font-size-gi-300',
            temporality='font-size-gi-200',
            real_value='font-size-gi-100',
            plan_value='font-size-gi-200',
            last_measurement_label='font-size-gi-400',
            last_measurement_value='font-size-gi-300',
        ),
        indicators=(
            IndicatorDefinition('Día', 'recuperacion_cu'),
            IndicatorDefinition('Semana', 'recuperacion_cu'),
            IndicatorDefinition('actual', 'recuperacion_cu', only_last_measurement=True),
        ),
    )
    data = map_global_indicator_data(
        definition=definition,
        kpis={
            'recuperacion_cu_dia_real_inst': '89,4',
            'recuperacion_cu_dia_plan_inst': '90,5',
            'recuperacion_cu_semana_real_inst': '89,1',
            'recuperacion_cu_semana_plan_inst': '90,5',
            'recuperacion_cu_actual_real_inst': '88,9',
        },
    )

    assert [item.temporality for item in data.indicators] == ['Día', 'Semana', 'Actual']
    assert data.indicators[-1].only_last_measurement is True
    assert data.indicators[-1].real_value == '88,9'
