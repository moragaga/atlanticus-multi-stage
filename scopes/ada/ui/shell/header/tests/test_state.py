from datetime import date

import pytest

from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ProcessBodySection,
    ToolScope,
    ToolSource,
    ToolSourceKey,
    build_process_manifest,
)
from ada.ui.components.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.components.global_indicator import (
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
)
from ada.ui.shell.header import (
    AlarmManagementSegmentState,
    AlarmManagementState,
    AlarmStatusState,
    HeaderDefinitionError,
    HeaderIndicatorPlacement,
    create_header_state,
)


def _brand():
    return resolve_brand(
        ATLANTICUS_BRAND_MANIFEST,
        BrandContext(current_date=date(2026, 8, 12)),
    )


def _placement(section_key: str, scope: ToolScope, *, last: bool = False):
    measurements = [
        GlobalIndicatorMeasurementState.temporal('100', temporality='Día', plan_value='105')
    ]
    if last:
        measurements.append(GlobalIndicatorMeasurementState.last_measurement('99'))
    return HeaderIndicatorPlacement(
        section_key=section_key,
        scope=scope,
        indicator=GlobalIndicatorState(
            key='recuperacion_cu',
            label='Recuperación Cu',
            unit='%',
            measurements=tuple(measurements),
        ),
    )


def test_integrated_operations_accepts_mine_and_plant_header_segments() -> None:
    state = create_header_state(
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
        brand=_brand(),
        application_name='ADA',
        global_indicators=(
            _placement('global_indicators_mine', ToolScope.MINE),
            HeaderIndicatorPlacement(
                section_key='global_indicators_plant',
                scope=ToolScope.PLANT,
                indicator=GlobalIndicatorState(
                    key='molienda',
                    label='Molienda',
                    unit='kt',
                    measurements=(
                        GlobalIndicatorMeasurementState.temporal(
                            '195',
                            temporality='Día',
                            plan_value='210',
                        ),
                    ),
                ),
            ),
        ),
        alarm_management=AlarmManagementState(
            segments=(
                AlarmManagementSegmentState(
                    'alarm_management_mine',
                    ToolScope.MINE,
                    'G3',
                    60,
                ),
                AlarmManagementSegmentState(
                    'alarm_management_plant',
                    ToolScope.PLANT,
                    'G1',
                    45,
                ),
            )
        ),
        alarm_status=AlarmStatusState(0, 0),
    )

    assert state.alarm_management is not None
    assert {item.scope for item in state.alarm_management.segments} == {
        ToolScope.MINE,
        ToolScope.PLANT,
    }


def test_chancado_process_header_uses_only_mine_management() -> None:
    manifest = build_process_manifest(
        tool_key='chancado_stmg',
        display_name='Chancado-STMG',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=300),),
        operational_scope=ToolScope.MINE,
        body_sections=(ProcessBodySection.CENTER,),
    )
    state = create_header_state(
        manifest=manifest,
        brand=_brand(),
        application_name='ADA',
        global_indicators=(_placement('global_indicators', ToolScope.MINE),),
        alarm_management=AlarmManagementState(
            segments=(
                AlarmManagementSegmentState(
                    'alarm_management',
                    ToolScope.MINE,
                    'G2',
                    70,
                ),
            )
        ),
        alarm_status=AlarmStatusState(1, 2),
    )

    assert state.alarm_management is not None
    assert state.alarm_management.segments[0].scope is ToolScope.MINE


def test_selective_flotation_header_accepts_last_measurement_and_plant_scope() -> None:
    manifest = build_process_manifest(
        tool_key='flotacion_selectiva',
        display_name='Flotación Selectiva',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=300),),
        operational_scope=ToolScope.PLANT,
        body_sections=(ProcessBodySection.CENTER,),
    )
    state = create_header_state(
        manifest=manifest,
        brand=_brand(),
        application_name='ADA',
        global_indicators=(_placement('global_indicators', ToolScope.PLANT, last=True),),
        alarm_management=AlarmManagementState(
            segments=(
                AlarmManagementSegmentState(
                    'alarm_management',
                    ToolScope.PLANT,
                    'G1',
                    50,
                ),
            )
        ),
        alarm_status=AlarmStatusState(0, 0),
    )

    indicator = state.global_indicators[0].indicator
    assert indicator.measurements[-1].is_last_measurement is True
    assert state.alarm_management is not None
    assert state.alarm_management.segments[0].scope is ToolScope.PLANT


def test_header_rejects_scope_that_disagrees_with_manifest() -> None:
    manifest = build_process_manifest(
        tool_key='flotacion_selectiva',
        display_name='Flotación Selectiva',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=300),),
        operational_scope=ToolScope.PLANT,
        body_sections=(ProcessBodySection.CENTER,),
    )

    with pytest.raises(HeaderDefinitionError, match='scope does not match'):
        create_header_state(
            manifest=manifest,
            brand=_brand(),
            application_name='ADA',
            global_indicators=(_placement('global_indicators', ToolScope.MINE),),
        )
