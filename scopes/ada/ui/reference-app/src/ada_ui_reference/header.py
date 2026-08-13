from datetime import date

from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST, ToolScope
from ada.ui.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.components.global_indicator import (
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
)
from ada.ui.components.state_wrapper import StateWrapperState
from ada.ui.header import (
    AlarmManagementSegmentState,
    AlarmManagementState,
    HeaderIndicatorPlacement,
    HeaderSectionStates,
    HeaderTone,
    create_header_state,
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
                    group='G3',
                    management_percentage=60,
                    tone=HeaderTone.ATTENTION,
                ),
                AlarmManagementSegmentState(
                    section_key='alarm_management_plant',
                    scope=ToolScope.PLANT,
                    group='G1',
                    management_percentage=45,
                    tone=HeaderTone.CRITICAL,
                ),
            )
        ),
        section_states=HeaderSectionStates(
            global_indicators=StateWrapperState.stale(),
            alarm_status=StateWrapperState.construction(),
        ),
    )


def _indicator(
    key: str,
    label: str,
    unit: str,
    scope: ToolScope,
    day_value: str,
    day_plan: str,
) -> HeaderIndicatorPlacement:
    section_key = {
        ToolScope.MINE: 'global_indicators_mine',
        ToolScope.PLANT: 'global_indicators_plant',
    }[scope]
    return HeaderIndicatorPlacement(
        section_key=section_key,
        scope=scope,
        indicator=GlobalIndicatorState(
            key=key,
            label=label,
            unit=unit,
            definition_key=key,
            measurements=(
                GlobalIndicatorMeasurementState.temporal(
                    day_value,
                    temporality='Día',
                    plan_value=day_plan,
                ),
                GlobalIndicatorMeasurementState.temporal(
                    day_value,
                    temporality='Semana',
                    plan_value=day_plan,
                ),
            ),
        ),
    )
