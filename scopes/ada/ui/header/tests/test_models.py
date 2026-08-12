import pytest

from ada.contracts.tool_manifest import ToolScope
from ada.ui.components.global_indicator import (
    GlobalIndicatorData,
    IndicatorData,
    IndicatorPropertiesData,
)
from ada.ui.header import (
    AlarmManagementSegmentState,
    AlarmManagementState,
    HeaderDefinitionError,
    HeaderGlobalIndicator,
)


def _indicator() -> GlobalIndicatorData:
    return GlobalIndicatorData(
        label='Transportado',
        unit='kt',
        properties=IndicatorPropertiesData(
            label='font-size-gi-300',
            temporality='font-size-gi-200',
            real_value='font-size-gi-100',
            plan_value='font-size-gi-200',
            last_measurement_label='font-size-gi-400',
            last_measurement_value='font-size-gi-300',
        ),
        indicators=(IndicatorData('198', temporality='Día', plan_value='220'),),
    )


def test_header_global_indicator_keeps_placement_outside_component_contract() -> None:
    placement = HeaderGlobalIndicator(
        key='transportado',
        section_key='global_indicators_mine',
        scope=ToolScope.MINE,
        indicator=_indicator(),
        definition_key='transportado',
    )

    assert placement.indicator.label == 'Transportado'
    assert placement.scope is ToolScope.MINE


def test_alarm_management_accepts_one_scope_for_process_tool() -> None:
    state = AlarmManagementState(
        segments=(
            AlarmManagementSegmentState(
                section_key='alarm_management',
                scope=ToolScope.PLANT,
                group_value='G1',
                management_percentage=45,
            ),
        )
    )

    assert len(state.segments) == 1


def test_alarm_management_rejects_global_segment() -> None:
    with pytest.raises(HeaderDefinitionError, match='must be mine or plant'):
        AlarmManagementSegmentState(
            section_key='alarm_management',
            scope=ToolScope.GLOBAL,
            group_value='G1',
            management_percentage=45,
        )
