from datetime import date

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
from ada.ui.components.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.components.global_indicator import (
    GlobalIndicatorLastMeasurementState,
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
)
from ada.ui.shell.header import HeaderDefinitionError, HeaderIndicatorPlacement, create_header_state


def _brand():
    return resolve_brand(
        ATLANTICUS_BRAND_MANIFEST,
        BrandContext(current_date=date(2026, 8, 12)),
    )


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


def _indicator(key: str = 'recuperacion_cu', *, last: bool = False) -> GlobalIndicatorState:
    return GlobalIndicatorState(
        key=key,
        label=key.replace('_', ' ').title(),
        unit='%',
        measurements=(
            GlobalIndicatorMeasurementState(
                key='turno',
                label='Turno',
                actual_value='100',
                plan_value='105',
            ),
            GlobalIndicatorMeasurementState(
                key='dia',
                label='Día',
                actual_value='101',
                plan_value='105',
            ),
        ),
        last_measurement=(GlobalIndicatorLastMeasurementState('99') if last else None),
    )


def _placement(section_key: str, scope: ToolScope, *, last: bool = False):
    return HeaderIndicatorPlacement(
        section_key=section_key,
        scopes=frozenset({scope}),
        indicator=_indicator(last=last),
    )


def test_integrated_operations_header_accepts_mine_plant_and_shared_indicators() -> None:
    state = create_header_state(
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
        brand=_brand(),
        application_name='ADA',
        global_indicators=(
            _placement(
                INTEGRATED_OPERATIONS_MANIFEST.subcomponent(
                    component='global_indicators',
                    subcomponent='mine',
                ).key,
                ToolScope.MINE,
            ),
            HeaderIndicatorPlacement(
                section_key=INTEGRATED_OPERATIONS_MANIFEST.subcomponent(
                    component='global_indicators',
                    subcomponent='plant',
                ).key,
                scopes=frozenset({ToolScope.PLANT}),
                indicator=_indicator('molienda'),
            ),
            HeaderIndicatorPlacement(
                section_key='global_indicators',
                scopes=frozenset({ToolScope.MINE, ToolScope.PLANT}),
                indicator=_indicator('cumplimiento_global'),
            ),
        ),
    )

    assert tuple(placement.scopes for placement in state.global_indicators) == (
        frozenset({ToolScope.MINE}),
        frozenset({ToolScope.PLANT}),
        frozenset({ToolScope.MINE, ToolScope.PLANT}),
    )


def test_process_header_accepts_optional_last_measurement_and_operational_scope() -> None:
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
    state = create_header_state(
        manifest=manifest,
        brand=_brand(),
        application_name='ADA',
        global_indicators=(_placement('global_indicators', ToolScope.PLANT, last=True),),
    )

    indicator = state.global_indicators[0].indicator
    assert indicator.last_measurement is not None
    assert indicator.last_measurement.key == 'latest'


def test_header_rejects_scope_that_disagrees_with_manifest() -> None:
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

    with pytest.raises(HeaderDefinitionError, match='scope does not match'):
        create_header_state(
            manifest=manifest,
            brand=_brand(),
            application_name='ADA',
            global_indicators=(_placement('global_indicators', ToolScope.MINE),),
        )


def test_process_header_rejects_shared_mine_plant_indicator() -> None:
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

    with pytest.raises(HeaderDefinitionError, match='must use global scope'):
        create_header_state(
            manifest=manifest,
            brand=_brand(),
            application_name='ADA',
            global_indicators=(
                HeaderIndicatorPlacement(
                    section_key='global_indicators',
                    scopes=frozenset({ToolScope.MINE, ToolScope.PLANT}),
                    indicator=_indicator(),
                ),
            ),
        )
