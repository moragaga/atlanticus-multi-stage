import pytest

from ada.ui.components.global_indicator import (
    GlobalIndicatorDefinitionError,
    GlobalIndicatorMeasurementKind,
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
    GlobalIndicatorStyle,
)


def test_global_indicator_style_has_reusable_defaults() -> None:
    style = GlobalIndicatorStyle()

    assert style.heading_class == 'font-size-gi-300'
    assert style.real_value_class == 'font-size-gi-100'


def test_global_indicator_state_uses_domain_names_and_default_style() -> None:
    state = GlobalIndicatorState(
        key='transportado',
        label='Transportado',
        unit='kt',
        measurements=(
            GlobalIndicatorMeasurementState.temporal('198', temporality='Día', plan_value='220'),
        ),
    )

    assert state.key == 'transportado'
    assert state.measurements[0].temporality == 'Día'
    assert state.style == GlobalIndicatorStyle()


def test_last_measurement_rejects_plan_value() -> None:
    with pytest.raises(GlobalIndicatorDefinitionError, match='cannot declare a plan value'):
        GlobalIndicatorMeasurementState(
            '88,9',
            plan_value='90,5',
            kind=GlobalIndicatorMeasurementKind.LAST_MEASUREMENT,
        )
