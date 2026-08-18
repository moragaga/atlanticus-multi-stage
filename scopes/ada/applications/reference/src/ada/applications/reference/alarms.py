from __future__ import annotations

from ada.contracts.tool_manifest import ToolManifest, ToolScope
from ada.features.alarms.management_summary import (
    AlarmManagementSummarySegmentState,
    AlarmManagementSummaryTone,
    build_alarm_management_summary,
    create_alarm_management_summary_state,
)
from ada.features.alarms.notifications import build_alarm_status
from ada.ui.components.state_wrapper import ComponentCover


def build_reference_alarm_management_summary(
    manifest: ToolManifest,
    *,
    cover: ComponentCover | None = None,
):
    state = create_alarm_management_summary_state(
        manifest=manifest,
        segments=(
            AlarmManagementSummarySegmentState(
                section_key=_alarm_management_section_key(manifest, ToolScope.MINE),
                scope=ToolScope.MINE,
                group='G3',
                management_percentage=60,
                tone=AlarmManagementSummaryTone.ATTENTION,
            ),
            AlarmManagementSummarySegmentState(
                section_key=_alarm_management_section_key(manifest, ToolScope.PLANT),
                scope=ToolScope.PLANT,
                group='G1',
                management_percentage=45,
                tone=AlarmManagementSummaryTone.CRITICAL,
            ),
        ),
    )
    return build_alarm_management_summary(
        state,
        cover=cover if cover is not None else ComponentCover.stale(),
    )


def _alarm_management_section_key(manifest: ToolManifest, scope: ToolScope) -> str:
    subcomponent = {
        ToolScope.MINE: 'mine',
        ToolScope.PLANT: 'plant',
    }[scope]
    return manifest.subcomponent(
        component='alarm_management',
        subcomponent=subcomponent,
    ).key


def build_reference_alarm_status(*, cover: ComponentCover | None = None):
    return build_alarm_status(
        None,
        cover=cover if cover is not None else ComponentCover.construction(),
    )
