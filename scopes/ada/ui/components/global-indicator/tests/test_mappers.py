from ada.ui.components.global_indicator import (
    GlobalIndicatorDefinition,
    GlobalIndicatorMeasurementDefinition,
    map_global_indicator_collection,
)
from ada.ui.framework.core import DisplayStatus


class RuntimeValue:
    def __init__(self, status, value=None):
        self.status = status
        self.value = value


def _definition() -> GlobalIndicatorDefinition:
    return GlobalIndicatorDefinition(
        key='recuperacion_cu',
        label='Recuperación Cu',
        unit='%',
        measurements=(
            GlobalIndicatorMeasurementDefinition.temporal('Día'),
            GlobalIndicatorMeasurementDefinition.temporal('Semana'),
        ),
    )


def test_mapper_keeps_configured_indicator_when_values_are_missing() -> None:
    collection = map_global_indicator_collection(definitions=(_definition(),), kpis={})
    indicator = collection.indicators[0]

    assert indicator.key == 'recuperacion_cu'
    assert indicator.measurements[0].real_value.status is DisplayStatus.NOT_MAPPED
    assert indicator.measurements[0].plan_value.status is DisplayStatus.NOT_MAPPED
    assert indicator.measurements[1].real_value.status is DisplayStatus.NOT_MAPPED


def test_mapper_accepts_runtime_style_value_states_without_runtime_dependency() -> None:
    collection = map_global_indicator_collection(
        definitions=(_definition(),),
        kpis={
            'recuperacion_cu_dia_real_inst': RuntimeValue('invalid'),
            'recuperacion_cu_dia_plan_inst': RuntimeValue('ok', '90,5'),
            'recuperacion_cu_semana_real_inst': RuntimeValue('empty'),
            'recuperacion_cu_semana_plan_inst': RuntimeValue('error'),
        },
    )
    indicator = collection.indicators[0]

    assert indicator.measurements[0].real_value.status is DisplayStatus.INVALID
    assert indicator.measurements[0].plan_value.value == '90,5'
    assert indicator.measurements[1].real_value.status is DisplayStatus.EMPTY
    assert indicator.measurements[1].plan_value.status is DisplayStatus.ERROR
