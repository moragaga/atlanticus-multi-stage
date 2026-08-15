import pytest

from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ProcessBodySection,
    ToolScope,
    ToolSection,
    ToolSectionKind,
    ToolSource,
    ToolSourceKey,
    ToolTarget,
    build_process_manifest,
)
from ada.ui.features.alarms import AlarmDefinitionError
from ada.ui.features.alarms.management_summary import (
    AlarmManagementSummarySegmentState,
    create_alarm_management_summary_state,
)
from ada.ui.features.alarms.notifications import create_alarm_status_state


def _process_center_component(
    *,
    key: str,
    display_name: str,
    scope: ToolScope,
) -> ToolSection:
    return ToolSection(
        key=key,
        display_name=display_name,
        kind=ToolSectionKind.COMPONENT,
        scope=scope,
        parent_key='body',
        targets=(ToolTarget.KPI, ToolTarget.ALARM),
        layout_role=ProcessBodySection.CENTER,
    )


def _process_center_card(*, component: str, subcomponent: str, scope: ToolScope) -> ToolSection:
    return ToolSection(
        component=component,
        subcomponent=subcomponent,
        display_name=subcomponent.replace('_', ' ').title(),
        kind=ToolSectionKind.SUBCOMPONENT,
        scope=scope,
        targets=(ToolTarget.ALARM,),
    )


def test_integrated_operations_management_summary_accepts_mine_and_plant() -> None:
    state = create_alarm_management_summary_state(
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
        segments=(
            AlarmManagementSummarySegmentState(
                INTEGRATED_OPERATIONS_MANIFEST.subcomponent(
                    component='alarm_management',
                    subcomponent='mine',
                ).key,
                ToolScope.MINE,
                'G3',
                60,
            ),
            AlarmManagementSummarySegmentState(
                INTEGRATED_OPERATIONS_MANIFEST.subcomponent(
                    component='alarm_management',
                    subcomponent='plant',
                ).key,
                ToolScope.PLANT,
                'G1',
                45,
            ),
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
        body_sections=(
            _process_center_component(
                key='proceso_chancado',
                display_name='Proceso Chancado',
                scope=ToolScope.MINE,
            ),
            _process_center_card(
                component='proceso_chancado',
                subcomponent='chancado_stmg',
                scope=ToolScope.MINE,
            ),
        ),
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
        body_sections=(
            _process_center_component(
                key='planta_molibdeno',
                display_name='Planta Molibdeno',
                scope=ToolScope.PLANT,
            ),
            _process_center_card(
                component='planta_molibdeno',
                subcomponent='proceso_molibdeno',
                scope=ToolScope.PLANT,
            ),
        ),
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
