from datetime import date

from ada.contracts.tool_manifest import ProcessBodySection, ToolScope, build_process_manifest
from ada.ui.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.components.global_indicator import (
    GlobalIndicatorData,
    IndicatorData,
    IndicatorPropertiesData,
)
from ada.ui.header import (
    AlarmManagementSegmentState,
    AlarmManagementState,
    AlarmStatusState,
    HeaderGlobalIndicator,
    build_ada_header,
    create_header_state,
)


def test_process_header_marks_indicator_and_management_with_operational_scope() -> None:
    manifest = build_process_manifest(
        tool_key='flotacion_selectiva',
        display_name='Flotación Selectiva',
        operational_scope=ToolScope.PLANT,
        body_sections=(ProcessBodySection.CENTER,),
    )
    state = create_header_state(
        manifest=manifest,
        brand=resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date(2026, 8, 12)),
        ),
        application_name='ADA',
        global_indicators=(
            HeaderGlobalIndicator(
                key='recuperacion_cu',
                section_key='global_indicators',
                scope=ToolScope.PLANT,
                indicator=GlobalIndicatorData(
                    label='Recuperación Cu',
                    unit='%',
                    properties=IndicatorPropertiesData(
                        label='font-size-gi-300',
                        temporality='font-size-gi-200',
                        real_value='font-size-gi-100',
                        plan_value='font-size-gi-200',
                        last_measurement_label='font-size-gi-400',
                        last_measurement_value='font-size-gi-300',
                    ),
                    indicators=(
                        IndicatorData('89,4', temporality='Día', plan_value='90,5'),
                        IndicatorData(
                            '88,9',
                            temporality='Actual',
                            only_last_measurement=True,
                        ),
                    ),
                ),
            ),
        ),
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

    component = build_ada_header(state)
    header_inner = component.children[0]
    indicators = header_inner.children[1]
    management = header_inner.children[2]
    status = header_inner.children[3]

    assert indicators.children[0].kwargs['data-scope'] == 'plant'
    assert management.children[0].kwargs['data-scope'] == 'plant'
    assert status.kwargs['data-scope'] == 'global'
