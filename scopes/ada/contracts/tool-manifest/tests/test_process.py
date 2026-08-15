import pytest

from ada.contracts.tool_manifest import (
    ProcessBodySection,
    ToolManifestError,
    ToolScope,
    ToolSection,
    ToolSectionKind,
    ToolSource,
    ToolSourceKey,
    ToolTarget,
    build_process_manifest,
)

_PI = ToolSource(ToolSourceKey.PI, stale_after_seconds=300)
_KPI = frozenset({ToolTarget.KPI})
_ALARM = frozenset({ToolTarget.ALARM})
_KPI_ALARM = frozenset({ToolTarget.KPI, ToolTarget.ALARM})


def _process_region(
    *,
    key: str,
    display_name: str,
    scope: ToolScope,
    role: ProcessBodySection,
) -> ToolSection:
    return ToolSection(
        key=key,
        display_name=display_name,
        kind=ToolSectionKind.REGION,
        scope=scope,
        parent_key='body',
        targets=_KPI_ALARM if role is ProcessBodySection.CENTER else _KPI,
        layout_role=role,
    )


def test_process_manifest_accepts_functional_center_only_and_plant_scope() -> None:
    center = _process_region(
        key='planta_molibdeno',
        display_name='Planta Molibdeno',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.CENTER,
    )
    manifest = build_process_manifest(
        tool_key='flotacion_selectiva',
        display_name='Flotación Selectiva',
        sources=(_PI,),
        operational_scope=ToolScope.PLANT,
        body_sections=(center,),
    )

    assert [section.key for section in manifest.children('body')] == ['planta_molibdeno']
    assert manifest.region_for_layout_role(ProcessBodySection.CENTER) is center
    assert manifest.source(ToolSourceKey.PI) is _PI
    assert not manifest.has_source(ToolSourceKey.DISPATCH)
    assert manifest.section('global_indicators').scope is ToolScope.PLANT
    assert manifest.section('alarm_management').scope is ToolScope.PLANT
    assert manifest.section('alarm_status').scope is ToolScope.GLOBAL
    assert manifest.require_target('planta_molibdeno', ToolTarget.KPI) is center
    assert manifest.require_target('planta_molibdeno', ToolTarget.ALARM) is center


def test_process_manifest_accepts_mine_scope_with_functional_center_name() -> None:
    manifest = build_process_manifest(
        tool_key='chancado_stmg',
        display_name='Chancado-STMG',
        sources=(_PI,),
        operational_scope=ToolScope.MINE,
        body_sections=(
            _process_region(
                key='proceso_chancado',
                display_name='Proceso Chancado',
                scope=ToolScope.MINE,
                role=ProcessBodySection.CENTER,
            ),
        ),
    )

    assert manifest.section('global_indicators').scope is ToolScope.MINE
    assert manifest.section('alarm_management').scope is ToolScope.MINE
    assert manifest.region_for_layout_role(ProcessBodySection.CENTER).key == 'proceso_chancado'


def test_process_manifest_maps_functional_regions_to_generic_layout_roles() -> None:
    regions = (
        _process_region(
            key='aguas_arriba',
            display_name='Aguas Arriba',
            scope=ToolScope.PLANT,
            role=ProcessBodySection.LEFT,
        ),
        _process_region(
            key='molienda',
            display_name='Molienda',
            scope=ToolScope.PLANT,
            role=ProcessBodySection.CENTER,
        ),
        _process_region(
            key='aguas_abajo',
            display_name='Aguas Abajo',
            scope=ToolScope.PLANT,
            role=ProcessBodySection.RIGHT,
        ),
        _process_region(
            key='indicadores_inferiores',
            display_name='Indicadores Inferiores',
            scope=ToolScope.PLANT,
            role=ProcessBodySection.BOTTOM,
        ),
    )
    manifest = build_process_manifest(
        tool_key='molienda_process',
        display_name='Molienda',
        sources=(_PI,),
        operational_scope=ToolScope.PLANT,
        body_sections=regions,
    )

    assert manifest.region_for_layout_role(ProcessBodySection.LEFT).key == 'aguas_arriba'
    assert manifest.region_for_layout_role(ProcessBodySection.CENTER).key == 'molienda'
    assert manifest.region_for_layout_role(ProcessBodySection.RIGHT).key == 'aguas_abajo'
    assert (
        manifest.region_for_layout_role(ProcessBodySection.BOTTOM).key == 'indicadores_inferiores'
    )

    kpi_keys = {section.key for section in manifest.sections_for_target(ToolTarget.KPI)}
    alarm_keys = {section.key for section in manifest.sections_for_target(ToolTarget.ALARM)}

    assert {
        'global_indicators',
        'time_status',
        'aguas_arriba',
        'molienda',
        'aguas_abajo',
        'indicadores_inferiores',
    } <= kpi_keys
    assert alarm_keys == {'global_indicators', 'time_status', 'molienda'}


def test_process_center_can_be_divided_into_alarm_components_and_subcomponents() -> None:
    center = _process_region(
        key='planta_molibdeno',
        display_name='Planta Molibdeno',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.CENTER,
    )
    component = ToolSection(
        key='recuperacion',
        display_name='Recuperación',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.PLANT,
        parent_key='planta_molibdeno',
        targets=_ALARM,
    )
    subcomponent = ToolSection(
        component='recuperacion',
        subcomponent='molibdeno',
        display_name='Molibdeno',
        kind=ToolSectionKind.SUBCOMPONENT,
        scope=ToolScope.PLANT,
        targets=_ALARM,
    )
    manifest = build_process_manifest(
        tool_key='flotacion_selectiva',
        display_name='Flotación Selectiva',
        sources=(_PI,),
        operational_scope=ToolScope.PLANT,
        body_sections=(center, component, subcomponent),
    )

    alarm_keys = {section.key for section in manifest.sections_for_target(ToolTarget.ALARM)}

    assert {'planta_molibdeno', 'recuperacion', 'recuperacion_molibdeno'} <= alarm_keys
    assert [section.key for section in manifest.path('recuperacion_molibdeno')] == [
        'body',
        'planta_molibdeno',
        'recuperacion',
        'recuperacion_molibdeno',
    ]


def test_process_global_indicators_and_time_status_are_indivisible_alarm_targets() -> None:
    manifest = build_process_manifest(
        tool_key='process',
        display_name='Process',
        sources=(_PI,),
        operational_scope=ToolScope.PLANT,
        body_sections=(
            _process_region(
                key='proceso',
                display_name='Proceso',
                scope=ToolScope.PLANT,
                role=ProcessBodySection.CENTER,
            ),
        ),
    )

    assert manifest.children('global_indicators') == ()
    assert manifest.children('time_status') == ()
    assert manifest.require_target('global_indicators', ToolTarget.ALARM)
    assert manifest.require_target('time_status', ToolTarget.ALARM)


def test_process_manifest_rejects_global_operational_scope() -> None:
    with pytest.raises(ToolManifestError, match='must be mine or plant'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            sources=(_PI,),
            operational_scope=ToolScope.GLOBAL,
            body_sections=(),
        )


def test_process_manifest_requires_center_layout_role() -> None:
    with pytest.raises(ToolManifestError, match='requires the center layout role'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            sources=(_PI,),
            operational_scope=ToolScope.MINE,
            body_sections=(
                _process_region(
                    key='aguas_arriba',
                    display_name='Aguas Arriba',
                    scope=ToolScope.MINE,
                    role=ProcessBodySection.LEFT,
                ),
            ),
        )


def test_process_manifest_rejects_duplicate_layout_roles() -> None:
    with pytest.raises(ToolManifestError, match='duplicate layout roles'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            sources=(_PI,),
            operational_scope=ToolScope.MINE,
            body_sections=(
                _process_region(
                    key='first_center',
                    display_name='First Center',
                    scope=ToolScope.MINE,
                    role=ProcessBodySection.CENTER,
                ),
                _process_region(
                    key='second_center',
                    display_name='Second Center',
                    scope=ToolScope.MINE,
                    role=ProcessBodySection.CENTER,
                ),
            ),
        )


def test_process_manifest_rejects_children_outside_center() -> None:
    left = _process_region(
        key='aguas_arriba',
        display_name='Aguas Arriba',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.LEFT,
    )
    center = _process_region(
        key='proceso',
        display_name='Proceso',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.CENTER,
    )
    invalid_child = ToolSection(
        key='left_component',
        display_name='Left Component',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.PLANT,
        parent_key='aguas_arriba',
        targets=_ALARM,
    )

    with pytest.raises(ToolManifestError, match='Only the center process region'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            sources=(_PI,),
            operational_scope=ToolScope.PLANT,
            body_sections=(left, center, invalid_child),
        )


def test_process_manifest_rejects_invalid_region_targets() -> None:
    invalid_center = ToolSection(
        key='proceso',
        display_name='Proceso',
        kind=ToolSectionKind.REGION,
        scope=ToolScope.PLANT,
        parent_key='body',
        targets=_KPI,
        layout_role=ProcessBodySection.CENTER,
    )

    with pytest.raises(ToolManifestError, match='invalid targets'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            sources=(_PI,),
            operational_scope=ToolScope.PLANT,
            body_sections=(invalid_center,),
        )


def test_process_manifest_rejects_center_children_with_kpi_targets() -> None:
    center = _process_region(
        key='proceso',
        display_name='Proceso',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.CENTER,
    )
    invalid_child = ToolSection(
        key='component',
        display_name='Component',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.PLANT,
        parent_key='proceso',
        targets=_KPI_ALARM,
    )

    with pytest.raises(ToolManifestError, match='must accept only alarm targets'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            sources=(_PI,),
            operational_scope=ToolScope.PLANT,
            body_sections=(center, invalid_child),
        )
