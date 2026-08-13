import pytest

from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ProcessBodySection,
    ToolScope,
    ToolSource,
    ToolSourceKey,
    build_process_manifest,
)
from ada.ui.features.alarms import AlarmDefinitionError
from ada.ui.features.alarms.management_summary import (
    AlarmManagementSummarySegmentState,
    create_alarm_management_summary_state,
)
from ada.ui.features.alarms.notifications import create_alarm_status_state


def test_integrated_operations_management_summary_accepts_mine_and_plant() -> None:
    state = create_alarm_management_summary_state(
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
        segments=(
            AlarmManagementSummarySegmentState('alarm_management_mine', ToolScope.MINE, 'G3', 60),
            AlarmManagementSummarySegmentState('alarm_management_plant', ToolScope.PLANT, 'G1', 45),
        ),
    )

    assert {segment.scope for segment in state.segments} == {
        ToolScope.MINE,
        ToolScope.PLANT,
    }


def test_process_management_summary_uses_operational_scope() -> None:
    manifest = build_process_manifest(
        tool_key='chancado_stmg',
        display_name='Chancado-STMG',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=300),),
        operational_scope=ToolScope.MINE,
        body_sections=(ProcessBodySection.CENTER,),
    )
    state = create_alarm_management_summary_state(
        manifest=manifest,
        segments=(
            AlarmManagementSummarySegmentState('alarm_management', ToolScope.MINE, 'G2', 70),
        ),
    )

    assert state.segments[0].scope is ToolScope.MINE


def test_management_summary_rejects_scope_that_disagrees_with_manifest() -> None:
    manifest = build_process_manifest(
        tool_key='flotacion_selectiva',
        display_name='Flotación Selectiva',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=300),),
        operational_scope=ToolScope.PLANT,
        body_sections=(ProcessBodySection.CENTER,),
    )

    with pytest.raises(AlarmDefinitionError, match='scope does not match'):
        create_alarm_management_summary_state(
            manifest=manifest,
            segments=(
                AlarmManagementSummarySegmentState('alarm_management', ToolScope.MINE, 'G1', 50),
            ),
        )


def test_alarm_status_validates_header_section() -> None:
    state = create_alarm_status_state(
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
        active_count=2,
        managed_count=1,
    )

    assert state.active_count == 2
    assert state.managed_count == 1
