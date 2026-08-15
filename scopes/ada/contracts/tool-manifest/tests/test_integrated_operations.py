from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ToolScope,
    ToolSourceKey,
    ToolTarget,
)


def test_integrated_operations_has_expected_top_level_sections() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    assert manifest.tool_key == 'integrated_operations'
    assert manifest.display_name == 'Operaciones Integradas'
    assert manifest.source(ToolSourceKey.PI).stale_after_seconds == 300
    assert manifest.source(ToolSourceKey.DISPATCH).stale_after_seconds == 600
    assert [section.key for section in manifest.roots()] == ['header', 'time_status', 'body']


def test_integrated_operations_preserves_macro_components_and_shared_component() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    assert [section.key for section in manifest.children('mine')] == [
        'general_mina',
        'carguio',
        'transporte',
        'carguio_transporte',
        'chancado_stmg',
    ]
    assert [section.key for section in manifest.children('plant')] == [
        'stock_chacay',
        'molienda',
        'flotacion',
        'transporte_fluidos',
        'puerto',
    ]


def test_integrated_operations_shared_component_links_carguio_and_transporte() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    assert [section.key for section in manifest.linked_components('carguio_transporte')] == [
        'carguio',
        'transporte',
    ]
    assert [section.key for section in manifest.linked_components('carguio')] == [
        'carguio_transporte'
    ]
    assert [section.key for section in manifest.linked_components('transporte')] == [
        'carguio_transporte'
    ]


def test_integrated_operations_subcomponent_keys_are_derived_internally() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    colectiva = manifest.subcomponent(component='flotacion', subcomponent='colectiva')
    selectiva = manifest.subcomponent(component='flotacion', subcomponent='selectiva')

    assert colectiva.key == 'flotacion_colectiva'
    assert colectiva.parent_key == 'flotacion'
    assert selectiva.key == 'flotacion_selectiva'
    assert [section.key for section in manifest.children('flotacion')] == [
        'flotacion_colectiva',
        'flotacion_selectiva',
    ]


def test_global_indicators_and_time_status_are_configurable_alarm_units() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    assert manifest.require_target('global_indicators', ToolTarget.KPI).scope is ToolScope.GLOBAL
    assert manifest.require_target('global_indicators', ToolTarget.ALARM).scope is ToolScope.GLOBAL
    assert manifest.require_target('time_status', ToolTarget.KPI).scope is ToolScope.GLOBAL
    assert manifest.require_target('time_status', ToolTarget.ALARM).scope is ToolScope.GLOBAL

    indicator_groups = manifest.children('global_indicators')
    assert [(section.key, section.scope) for section in indicator_groups] == [
        ('global_indicators_mine', ToolScope.MINE),
        ('global_indicators_plant', ToolScope.PLANT),
    ]
    assert all(section.accepts(ToolTarget.KPI) for section in indicator_groups)
    assert all(not section.accepts(ToolTarget.ALARM) for section in indicator_groups)


def test_alarm_management_groups_remain_structural_and_not_alarm_targets() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    management_groups = manifest.children('alarm_management')

    assert [(section.key, section.scope) for section in management_groups] == [
        ('alarm_management_mine', ToolScope.MINE),
        ('alarm_management_plant', ToolScope.PLANT),
    ]
    assert all(not section.accepts(ToolTarget.ALARM) for section in management_groups)


def test_kpi_configuration_accepts_all_integrated_operations_components() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST
    keys = {section.key for section in manifest.sections_for_target(ToolTarget.KPI)}

    expected_components = {
        'general_mina',
        'carguio',
        'transporte',
        'carguio_transporte',
        'chancado_stmg',
        'stock_chacay',
        'molienda',
        'flotacion',
        'transporte_fluidos',
        'puerto',
    }

    assert expected_components <= keys
    assert {'global_indicators', 'time_status'} <= keys
    assert 'flotacion_colectiva' not in keys
    assert 'flotacion_selectiva' not in keys
    assert 'alarm_management' not in keys
    assert 'alarm_status' not in keys


def test_alarm_configuration_accepts_components_and_real_subcomponents() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST
    keys = {section.key for section in manifest.sections_for_target(ToolTarget.ALARM)}

    expected_components = {
        'general_mina',
        'carguio',
        'transporte',
        'carguio_transporte',
        'chancado_stmg',
        'stock_chacay',
        'molienda',
        'flotacion',
        'transporte_fluidos',
        'puerto',
    }

    assert expected_components <= keys
    assert {'global_indicators', 'time_status'} <= keys
    assert {'flotacion_colectiva', 'flotacion_selectiva'} <= keys
    assert 'global_indicators_mine' not in keys
    assert 'global_indicators_plant' not in keys
    assert 'alarm_management_mine' not in keys
    assert 'alarm_management_plant' not in keys
    assert 'alarm_status' not in keys


def test_section_path_is_semantic_and_independent_from_dom_ids() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    assert [section.key for section in manifest.path('flotacion_selectiva')] == [
        'body',
        'plant',
        'flotacion',
        'flotacion_selectiva',
    ]
