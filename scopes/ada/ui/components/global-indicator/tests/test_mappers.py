from ada.ui.components.global_indicator import (
    GlobalIndicatorDefinition,
    GlobalIndicatorLastMeasurementDefinition,
    GlobalIndicatorMeasurementDefinition,
    map_global_indicator_collection,
)
from ada.ui.framework.core import DisplayStatus


class RuntimeValue:
    def __init__(self, status, value=None):
        self.status = status
        self.value = value


def _definition(*, with_last: bool = False) -> GlobalIndicatorDefinition:
    return GlobalIndicatorDefinition(
        key='recuperacion_cu',
        label='Recuperación Cu',
        unit='%',
        measurements=(
            GlobalIndicatorMeasurementDefinition(key='dia', label='Día'),
            GlobalIndicatorMeasurementDefinition(key='semana', label='Semana'),
        ),
        last_measurement=(GlobalIndicatorLastMeasurementDefinition() if with_last else None),
    )


def test_mapper_keeps_configured_indicator_when_values_are_missing() -> None:
    collection = map_global_indicator_collection(definitions=(_definition(),), kpis={})
    indicator = collection.indicators[0]

    assert indicator.key == 'recuperacion_cu'
    assert indicator.measurements[0].actual_value.status is DisplayStatus.NOT_MAPPED
    assert indicator.measurements[0].plan_value.status is DisplayStatus.NOT_MAPPED
    assert indicator.measurements[1].actual_value.status is DisplayStatus.NOT_MAPPED
    assert indicator.last_measurement is None


def test_mapper_accepts_runtime_style_value_states_without_runtime_dependency() -> None:
    collection = map_global_indicator_collection(
        definitions=(_definition(with_last=True),),
        kpis={
            'recuperacion_cu_dia_real_inst': RuntimeValue('invalid'),
            'recuperacion_cu_dia_plan_inst': RuntimeValue('ok', '90,5'),
            'recuperacion_cu_semana_real_inst': RuntimeValue('empty'),
            'recuperacion_cu_semana_plan_inst': RuntimeValue('error'),
            'recuperacion_cu_latest_real_inst': RuntimeValue('ok', '88,9'),
        },
    )
    indicator = collection.indicators[0]

    assert indicator.measurements[0].actual_value.status is DisplayStatus.INVALID
    assert indicator.measurements[0].plan_value.value == '90,5'
    assert indicator.measurements[1].actual_value.status is DisplayStatus.EMPTY
    assert indicator.measurements[1].plan_value.status is DisplayStatus.ERROR
    assert indicator.last_measurement is not None
    assert indicator.last_measurement.actual_value.value == '88,9'
