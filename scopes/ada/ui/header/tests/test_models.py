import pytest

from ada.contracts.tool_manifest import ToolScope
from ada.ui.components.state_wrapper import DataFreshness, StateWrapperState
from ada.ui.header import (
    AlarmManagementSegmentState,
    AlarmManagementState,
    AlarmStatusState,
    HeaderDefinitionError,
    HeaderSectionStates,
)


def test_alarm_management_accepts_mine_and_plant() -> None:
    state = AlarmManagementState(
        segments=(
            AlarmManagementSegmentState('alarm_management_mine', ToolScope.MINE, 'G3', 60),
            AlarmManagementSegmentState('alarm_management_plant', ToolScope.PLANT, 'G1', 45),
        )
    )

    assert len(state.segments) == 2


def test_alarm_management_rejects_duplicate_scope() -> None:
    with pytest.raises(HeaderDefinitionError, match='duplicate scopes'):
        AlarmManagementState(
            segments=(
                AlarmManagementSegmentState('first', ToolScope.MINE, 'G1', 20),
                AlarmManagementSegmentState('second', ToolScope.MINE, 'G2', 40),
            )
        )


def test_alarm_status_rejects_negative_counts() -> None:
    with pytest.raises(HeaderDefinitionError, match='cannot be negative'):
        AlarmStatusState(-1, 0)


def test_header_section_states_can_mark_whole_global_indicator_collection_stale() -> None:
    states = HeaderSectionStates(global_indicators=StateWrapperState.stale())

    assert states.global_indicators.freshness is DataFreshness.STALE
