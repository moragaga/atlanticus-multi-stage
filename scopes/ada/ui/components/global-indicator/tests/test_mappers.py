from ada.ui.components.global_indicator import (
    GlobalIndicatorDefinition,
    GlobalIndicatorMeasurementDefinition,
    map_global_indicator_state,
)


def test_mapper_supports_last_measurement_without_special_tool_logic() -> None:
    definition = GlobalIndicatorDefinition(
        key='recuperacion_cu',
        label='Recuperación Cu',
        unit='%',
        definition_key='recuperacion_cu',
        measurements=(
            GlobalIndicatorMeasurementDefinition.temporal('Día'),
            GlobalIndicatorMeasurementDefinition.temporal('Semana'),
            GlobalIndicatorMeasurementDefinition.last_measurement(),
        ),
    )
    state = map_global_indicator_state(
        definition=definition,
        kpis={
            'recuperacion_cu_dia_real_inst': '89,4',
            'recuperacion_cu_dia_plan_inst': '90,5',
            'recuperacion_cu_semana_real_inst': '89,1',
            'recuperacion_cu_semana_plan_inst': '90,5',
            'recuperacion_cu_actual_real_inst': '88,9',
        },
    )

    assert [item.temporality for item in state.measurements] == ['Día', 'Semana', None]
    assert state.measurements[-1].is_last_measurement is True
    assert state.measurements[-1].real_value == '88,9'
    assert state.definition_key == 'recuperacion_cu'
