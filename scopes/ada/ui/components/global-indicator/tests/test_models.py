import pytest

from ada.ui.components.global_indicator import (
    GlobalIndicatorDefinitionError,
    GlobalIndicatorLastMeasurementState,
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
    GlobalIndicatorStyle,
    global_indicator_measurement_capacity,
)


def _measurement(key: str, label: str) -> GlobalIndicatorMeasurementState:
    return GlobalIndicatorMeasurementState(
        key=key,
        label=label,
        actual_value='198',
        plan_value='220',
    )


def test_global_indicator_style_has_reusable_defaults() -> None:
    style = GlobalIndicatorStyle()

    assert style.heading_class == 'font-size-gi-300'
    assert style.actual_value_class == 'font-size-gi-100'
    assert style.measurement_label_class == 'font-size-gi-200'


def test_global_indicator_state_uses_generic_measurement_identity() -> None:
    state = GlobalIndicatorState(
        key='transportado',
        label='Transportado',
        unit='kt',
        measurements=(
            _measurement('turno', 'Turno'),
            _measurement('dia', 'Día'),
        ),
    )

    assert state.key == 'transportado'
    assert state.measurement_keys == ('turno', 'dia')
    assert state.all_measurement_keys == ('turno', 'dia')
    assert state.style == GlobalIndicatorStyle()


def test_global_indicator_accepts_three_measurements_and_optional_last_measurement() -> None:
    state = GlobalIndicatorState(
        key='transportado',
        label='Transportado',
        unit='kt',
        measurements=(
            _measurement('turno', 'Turno'),
            _measurement('dia', 'Día'),
            _measurement('semana', 'Semana'),
        ),
        last_measurement=GlobalIndicatorLastMeasurementState('201'),
    )

    assert global_indicator_measurement_capacity() == 3
    assert state.all_measurement_keys == ('turno', 'dia', 'semana', 'latest')


def test_global_indicator_rejects_less_than_two_measurements() -> None:
    with pytest.raises(GlobalIndicatorDefinitionError, match='two or three measurements'):
        GlobalIndicatorState(
            key='transportado',
            label='Transportado',
            unit='kt',
            measurements=(_measurement('dia', 'Día'),),
        )


def test_global_indicator_rejects_more_than_three_measurements() -> None:
    with pytest.raises(GlobalIndicatorDefinitionError, match='two or three measurements'):
        GlobalIndicatorState(
            key='transportado',
            label='Transportado',
            unit='kt',
            measurements=(
                _measurement('turno', 'Turno'),
                _measurement('dia', 'Día'),
                _measurement('semana', 'Semana'),
                _measurement('mes', 'Mes'),
            ),
        )


def test_last_measurement_key_cannot_collide_with_normal_measurement() -> None:
    with pytest.raises(GlobalIndicatorDefinitionError, match='last measurement key must be unique'):
        GlobalIndicatorState(
            key='transportado',
            label='Transportado',
            unit='kt',
            measurements=(
                _measurement('latest', 'Último'),
                _measurement('dia', 'Día'),
            ),
            last_measurement=GlobalIndicatorLastMeasurementState('201'),
        )
