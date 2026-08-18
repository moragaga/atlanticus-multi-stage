from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ToolScope,
    ToolSourceKey,
    ToolTarget,
)

_EXPECTED_SUBCOMPONENTS = {
    'general_mina': ('movimiento_mina', 'remanentes', 'perforacion', 'mp10'),
    'carguio': ('equipos_servicio', 'mezcla_hacia_chancado', 'gestion_carguio_turno'),
    'transporte': ('transporte_global', 'numero_operativos', 'tiempos_y_colas'),
    'chancado_stmg': ('chancado_stmg',),
    'stockpile_chacay': ('stockpile_chacay', 'tendencia_alimentado'),
    'molienda': ('molienda',),
    'flotacion': ('colectiva', 'selectiva'),
    'transporte_fluidos': ('str', 'stc', 'tranque', 'sta'),
    'puerto': ('puerto', 'desaladora'),
}


def test_integrated_operations_has_expected_top_level_sections() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    assert manifest.tool_key == 'integrated_operations'
    assert manifest.display_name == 'Operaciones Integradas'
    assert manifest.source(ToolSourceKey.PI).stale_after_seconds == 300
    assert manifest.source(ToolSourceKey.DISPATCH).stale_after_seconds == 600
    assert [section.key for section in manifest.roots()] == ['header', 'time_status', 'body']


def test_integrated_operations_preserves_nine_real_macro_components() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    assert [section.key for section in manifest.children('mine')] == [
        'general_mina',
        'carguio',
        'transporte',
        'chancado_stmg',
    ]
    assert [section.key for section in manifest.children('plant')] == [
        'stockpile_chacay',
        'molienda',
        'flotacion',
        'transporte_fluidos',
        'puerto',
    ]


def test_integrated_operations_shared_card_is_one_subcomponent_for_both_components() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    from_carguio = manifest.subcomponent(
        component='carguio',
        subcomponent='gestion_carguio_turno',
    )
    from_transporte = manifest.subcomponent(
        component='transporte',
        subcomponent='gestion_carguio_turno',
    )

    assert from_carguio is from_transporte
    assert from_carguio.key == 'carguio_gestion_carguio_turno'
    assert from_carguio.parent_key == 'carguio'
    assert [section.key for section in manifest.linked_components(from_carguio.key)] == [
        'carguio',
        'transporte',
    ]


def test_integrated_operations_declares_all_real_component_cards() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    for component, subcomponents in _EXPECTED_SUBCOMPONENTS.items():
        sections = manifest.children(component)
        assert [section.subcomponent for section in sections] == list(subcomponents)
        assert [section.key for section in sections] == [
            f'{component}_{subcomponent}' for subcomponent in subcomponents
        ]

    assert sum(len(items) for items in _EXPECTED_SUBCOMPONENTS.values()) == 22


def test_integrated_operations_subcomponent_keys_are_derived_internally() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    colectiva = manifest.subcomponent(component='flotacion', subcomponent='colectiva')
    selectiva = manifest.subcomponent(component='flotacion', subcomponent='selectiva')

    assert colectiva.key == 'flotacion_colectiva'
    assert colectiva.parent_key == 'flotacion'
    assert selectiva.key == 'flotacion_selectiva'


def test_global_indicators_and_time_status_are_kpi_only_targets() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST

    assert manifest.require_target('global_indicators', ToolTarget.KPI).scope is ToolScope.GLOBAL
    assert not manifest.section('global_indicators').accepts(ToolTarget.ALARM)
    assert manifest.require_target('time_status', ToolTarget.KPI).scope is ToolScope.GLOBAL
    assert not manifest.section('time_status').accepts(ToolTarget.ALARM)

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
    expected_components = set(_EXPECTED_SUBCOMPONENTS)

    assert expected_components <= keys
    assert {'global_indicators', 'time_status'} <= keys
    assert all(
        f'{component}_{subcomponent}' not in keys
        for component, subcomponents in _EXPECTED_SUBCOMPONENTS.items()
        for subcomponent in subcomponents
    )
    assert 'alarm_management' not in keys
    assert 'alarm_status' not in keys


def test_alarm_configuration_accepts_all_components_and_real_subcomponents() -> None:
    manifest = INTEGRATED_OPERATIONS_MANIFEST
    keys = {section.key for section in manifest.sections_for_target(ToolTarget.ALARM)}
    expected_components = set(_EXPECTED_SUBCOMPONENTS)
    expected_subcomponents = {
        f'{component}_{subcomponent}'
        for component, subcomponents in _EXPECTED_SUBCOMPONENTS.items()
        for subcomponent in subcomponents
    }

    assert expected_components <= keys
    assert expected_subcomponents <= keys
    assert 'global_indicators' not in keys
    assert 'time_status' not in keys
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
    assert [section.key for section in manifest.path('stockpile_chacay_tendencia_alimentado')] == [
        'body',
        'plant',
        'stockpile_chacay',
        'stockpile_chacay_tendencia_alimentado',
    ]
