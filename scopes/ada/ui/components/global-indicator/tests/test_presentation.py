from ada.ui.components.global_indicator import (
    GlobalIndicatorData,
    IndicatorData,
    IndicatorPropertiesData,
    build_global_indicator,
)


def test_presentation_keeps_last_measurement_inside_same_component() -> None:
    model = GlobalIndicatorData(
        label='Recuperación Cu',
        unit='%',
        properties=IndicatorPropertiesData(
            label='font-size-gi-300',
            temporality='font-size-gi-200',
            real_value='font-size-gi-100',
            plan_value='font-size-gi-200',
            last_measurement_label='font-size-gi-400',
            last_measurement_value='font-size-gi-300',
        ),
        indicators=(
            IndicatorData('89,4', temporality='Día', plan_value='90,5'),
            IndicatorData('89,1', temporality='Semana', plan_value='90,5'),
            IndicatorData('88,9', temporality='Actual', only_last_measurement=True),
        ),
    )

    component = build_global_indicator(model=model)
    content = component.children[1]
    table, last_measurement = content.children

    assert component.className == 'global-indicator'
    assert table.className == 'global-indicator__table'
    assert last_measurement.className == 'global-indicator__last-measurement'
