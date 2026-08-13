import pytest

from ada.contracts.tool_manifest import ToolScope
from ada.ui.features.alarms import AlarmDefinitionError
from ada.ui.features.alarms.management_summary import (
    AlarmManagementSummarySegmentState,
    AlarmManagementSummaryState,
)
from ada.ui.features.alarms.notifications import AlarmStatusState


def test_management_summary_accepts_mine_and_plant() -> None:
    state = AlarmManagementSummaryState(
        segments=(
            AlarmManagementSummarySegmentState('alarm_management_mine', ToolScope.MINE, 'G3', 60),
            AlarmManagementSummarySegmentState('alarm_management_plant', ToolScope.PLANT, 'G1', 45),
        )
    )

    assert len(state.segments) == 2


def test_management_summary_rejects_duplicate_scope() -> None:
    with pytest.raises(AlarmDefinitionError, match='duplicate scopes'):
        AlarmManagementSummaryState(
            segments=(
                AlarmManagementSummarySegmentState('first', ToolScope.MINE, 'G1', 20),
                AlarmManagementSummarySegmentState('second', ToolScope.MINE, 'G2', 40),
            )
        )


def test_alarm_status_rejects_negative_counts() -> None:
    with pytest.raises(AlarmDefinitionError, match='cannot be negative'):
        AlarmStatusState(-1, 0)
