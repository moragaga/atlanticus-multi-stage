from ada.ui.components.global_indicator import (
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
    build_global_indicator,
)


def test_presentation_keeps_last_measurement_inside_same_component() -> None:
    state = GlobalIndicatorState(
        key='recuperacion_cu',
        label='Recuperación Cu',
        unit='%',
        measurements=(
            GlobalIndicatorMeasurementState.temporal('89,4', temporality='Día', plan_value='90,5'),
            GlobalIndicatorMeasurementState.temporal(
                '89,1',
                temporality='Semana',
                plan_value='90,5',
            ),
            GlobalIndicatorMeasurementState.last_measurement('88,9'),
        ),
    )

    component = build_global_indicator(state=state)
    content = component.children[1]
    table, last_measurement = content.children

    assert component.className == 'global-indicator'
    assert table.className == 'global-indicator__table'
    assert last_measurement.className == 'global-indicator__last-measurement'
