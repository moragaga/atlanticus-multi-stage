from datetime import date

from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST, ToolScope
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
    HeaderTone,
    create_header_state,
)

_PROPERTIES = IndicatorPropertiesData(
    label='font-size-gi-300',
    temporality='font-size-gi-200',
    real_value='font-size-gi-100',
    plan_value='font-size-gi-200',
    last_measurement_label='font-size-gi-400',
    last_measurement_value='font-size-gi-300',
)


def build_reference_header_state():
    return create_header_state(
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
        brand=resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date.today()),
        ),
        application_name='ADA',
        global_indicators=(
            _indicator('transportado', 'Transportado', 'kt', ToolScope.MINE, '198', '220'),
            _indicator('molienda', 'Molienda', 'kt', ToolScope.PLANT, '195', '210'),
            _indicator('ley_cobre', 'Ley de Cobre', '%', ToolScope.PLANT, '0,52', '0,55'),
            _indicator(
                'recuperacion_cu',
                'Recuperación Cu',
                '%',
                ToolScope.PLANT,
                '89,4',
                '90,5',
            ),
            _indicator(
                'cu_fino_producido',
                'Cu Fino Producido',
                't',
                ToolScope.PLANT,
                '920',
                '1.050',
            ),
            _indicator(
                'mo_fino_producido',
                'Mo Fino Producido',
                't',
                ToolScope.PLANT,
                '28',
                '33',
            ),
            _indicator('expit', 'ExPit', 't', ToolScope.MINE, '376', '426'),
            _indicator(
                'cu_fino_filtrado_pagable',
                'Cu Fino Filtr. Pag.',
                't',
                ToolScope.PLANT,
                '1.886',
                '1.784',
            ),
        ),
        alarm_management=AlarmManagementState(
            segments=(
                AlarmManagementSegmentState(
                    section_key='alarm_management_mine',
                    scope=ToolScope.MINE,
                    group_value='G3',
                    management_percentage=60,
                    tone=HeaderTone.ATTENTION,
                ),
                AlarmManagementSegmentState(
                    section_key='alarm_management_plant',
                    scope=ToolScope.PLANT,
                    group_value='G1',
                    management_percentage=45,
                    tone=HeaderTone.CRITICAL,
                ),
            )
        ),
        alarm_status=AlarmStatusState(active_count=0, managed_count=0),
    )


def _indicator(
    key: str,
    label: str,
    unit: str,
    scope: ToolScope,
    day_value: str,
    day_plan: str,
) -> HeaderGlobalIndicator:
    section_key = {
        ToolScope.MINE: 'global_indicators_mine',
        ToolScope.PLANT: 'global_indicators_plant',
    }[scope]
    return HeaderGlobalIndicator(
        key=key,
        section_key=section_key,
        scope=scope,
        definition_key=key,
        indicator=GlobalIndicatorData(
            label=label,
            unit=unit,
            properties=_PROPERTIES,
            indicators=(
                IndicatorData(day_value, temporality='Día', plan_value=day_plan),
                IndicatorData(day_value, temporality='Semana', plan_value=day_plan),
            ),
        ),
    )
