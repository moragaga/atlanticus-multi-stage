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


def test_integrated_operations_preserves_expandable_mine_and_plant_groups() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    assert [section.key for section in manifest.children('mine')] == [
        'general_mina',
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


def test_integrated_operations_exposes_real_subcomponents() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    assert [section.key for section in manifest.children('carguio_transporte')] == [
        'carguio',
        'transporte',
    ]
    assert [section.key for section in manifest.children('flotacion')] == [
        'flotacion_colectiva',
        'flotacion_selectiva',
    ]


def test_header_groups_expose_mine_and_plant_without_becoming_alarm_targets() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    indicator_groups = manifest.children('global_indicators')
    management_groups = manifest.children('alarm_management')

    assert [(section.key, section.scope) for section in indicator_groups] == [
        ('global_indicators_mine', ToolScope.MINE),
        ('global_indicators_plant', ToolScope.PLANT),
    ]
    assert [(section.key, section.scope) for section in management_groups] == [
        ('alarm_management_mine', ToolScope.MINE),
        ('alarm_management_plant', ToolScope.PLANT),
    ]
    assert all(not section.accepts(ToolTarget.ALARM) for section in management_groups)


def test_kpi_configuration_can_query_only_valid_kpi_targets() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    keys = {section.key for section in manifest.sections_for_target(ToolTarget.KPI)}

    assert 'global_indicators_mine' in keys
    assert 'global_indicators_plant' in keys
    assert 'flotacion_selectiva' in keys
    assert 'time_status' not in keys
    assert 'alarm_management' not in keys
    assert 'alarm_status' not in keys


def test_falarm_can_query_body_alarm_targets_without_header_summary_sections() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    keys = {section.key for section in manifest.sections_for_target(ToolTarget.ALARM)}

    assert 'general_mina' in keys
    assert 'carguio_transporte' in keys
    assert 'carguio' in keys
    assert 'transporte' in keys
    assert 'flotacion' in keys
    assert 'flotacion_colectiva' in keys
    assert 'flotacion_selectiva' in keys
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
