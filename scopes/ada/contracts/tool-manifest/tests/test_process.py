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


def _component(
    *,
    key: str,
    display_name: str,
    scope: ToolScope,
    role: ProcessBodySection,
) -> ToolSection:
    return ToolSection(
        key=key,
        display_name=display_name,
        kind=ToolSectionKind.COMPONENT,
        scope=scope,
        parent_key='body',
        targets=_KPI_ALARM if role is ProcessBodySection.CENTER else _KPI,
        layout_role=role,
    )


def _subcomponent(
    *,
    component: str,
    subcomponent: str,
    display_name: str,
    scope: ToolScope,
    alarm: bool = False,
) -> ToolSection:
    return ToolSection(
        component=component,
        subcomponent=subcomponent,
        display_name=display_name,
        kind=ToolSectionKind.SUBCOMPONENT,
        scope=scope,
        targets=_ALARM if alarm else (),
    )


def test_process_manifest_accepts_center_component_with_multiple_cards() -> None:
    center = _component(
        key='planta_molibdeno',
        display_name='Planta Molibdeno',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.CENTER,
    )
    rougher = _subcomponent(
        component='planta_molibdeno',
        subcomponent='rougher',
        display_name='Rougher',
        scope=ToolScope.PLANT,
        alarm=True,
    )
    cleaner = _subcomponent(
        component='planta_molibdeno',
        subcomponent='cleaner',
        display_name='Cleaner',
        scope=ToolScope.PLANT,
        alarm=True,
    )
    manifest = build_process_manifest(
        tool_key='flotacion_selectiva',
        display_name='Flotación Selectiva',
        sources=(_PI,),
        operational_scope=ToolScope.PLANT,
        body_sections=(center, rougher, cleaner),
    )

    assert manifest.children('body') == (center,)
    assert manifest.component_for_layout_role(ProcessBodySection.CENTER) is center
    assert manifest.children('planta_molibdeno') == (rougher, cleaner)
    assert [section.key for section in manifest.path('planta_molibdeno_rougher')] == [
        'body',
        'planta_molibdeno',
        'planta_molibdeno_rougher',
    ]
    assert manifest.require_target('planta_molibdeno', ToolTarget.KPI) is center
    assert manifest.require_target('planta_molibdeno', ToolTarget.ALARM) is center
    assert manifest.require_target('planta_molibdeno_rougher', ToolTarget.ALARM) is rougher


def test_process_manifest_accepts_left_center_right_and_single_bottom_card() -> None:
    left = _component(
        key='aguas_arriba',
        display_name='Aguas Arriba',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.LEFT,
    )
    center = _component(
        key='planta_molibdeno',
        display_name='Planta Molibdeno',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.CENTER,
    )
    right = _component(
        key='aguas_abajo',
        display_name='Aguas Abajo',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.RIGHT,
    )
    bottom = _component(
        key='graficas_tendencia',
        display_name='Gráficas Tendencia',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.BOTTOM,
    )
    sections = (
        left,
        center,
        right,
        bottom,
        _subcomponent(
            component='aguas_arriba',
            subcomponent='flotacion_colectiva',
            display_name='Flotación Colectiva',
            scope=ToolScope.PLANT,
        ),
        _subcomponent(
            component='aguas_arriba',
            subcomponent='tendencias_courier',
            display_name='Tendencias Courier',
            scope=ToolScope.PLANT,
        ),
        _subcomponent(
            component='planta_molibdeno',
            subcomponent='rougher',
            display_name='Rougher',
            scope=ToolScope.PLANT,
            alarm=True,
        ),
        _subcomponent(
            component='planta_molibdeno',
            subcomponent='cleaner',
            display_name='Cleaner',
            scope=ToolScope.PLANT,
            alarm=True,
        ),
        _subcomponent(
            component='aguas_abajo',
            subcomponent='stc',
            display_name='STC',
            scope=ToolScope.PLANT,
        ),
        _subcomponent(
            component='aguas_abajo',
            subcomponent='plf',
            display_name='PLF',
            scope=ToolScope.PLANT,
        ),
        _subcomponent(
            component='graficas_tendencia',
            subcomponent='graficas',
            display_name='Gráficas',
            scope=ToolScope.PLANT,
        ),
    )
    manifest = build_process_manifest(
        tool_key='flotacion_selectiva',
        display_name='Flotación Selectiva',
        sources=(_PI,),
        operational_scope=ToolScope.PLANT,
        body_sections=sections,
    )

    assert [section.key for section in manifest.children('body')] == [
        'aguas_arriba',
        'planta_molibdeno',
        'aguas_abajo',
        'graficas_tendencia',
    ]
    assert [section.subcomponent for section in manifest.children('aguas_arriba')] == [
        'flotacion_colectiva',
        'tendencias_courier',
    ]
    assert [section.subcomponent for section in manifest.children('planta_molibdeno')] == [
        'rougher',
        'cleaner',
    ]
    assert [section.subcomponent for section in manifest.children('graficas_tendencia')] == [
        'graficas'
    ]

    alarm_keys = {section.key for section in manifest.sections_for_target(ToolTarget.ALARM)}
    assert {
        'global_indicators',
        'time_status',
        'planta_molibdeno',
        'planta_molibdeno_rougher',
        'planta_molibdeno_cleaner',
    } <= alarm_keys
    assert 'aguas_arriba_flotacion_colectiva' not in alarm_keys
    assert 'aguas_abajo_stc' not in alarm_keys
    assert 'graficas_tendencia_graficas' not in alarm_keys


def test_process_global_indicators_and_time_status_are_indivisible_alarm_targets() -> None:
    center = _component(
        key='proceso',
        display_name='Proceso',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.CENTER,
    )
    card = _subcomponent(
        component='proceso',
        subcomponent='principal',
        display_name='Principal',
        scope=ToolScope.PLANT,
        alarm=True,
    )
    manifest = build_process_manifest(
        tool_key='process',
        display_name='Process',
        sources=(_PI,),
        operational_scope=ToolScope.PLANT,
        body_sections=(center, card),
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
    left = _component(
        key='aguas_arriba',
        display_name='Aguas Arriba',
        scope=ToolScope.MINE,
        role=ProcessBodySection.LEFT,
    )
    left_card = _subcomponent(
        component='aguas_arriba',
        subcomponent='principal',
        display_name='Principal',
        scope=ToolScope.MINE,
    )
    with pytest.raises(ToolManifestError, match='requires the center layout role'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            sources=(_PI,),
            operational_scope=ToolScope.MINE,
            body_sections=(left, left_card),
        )


def test_process_manifest_rejects_duplicate_layout_roles() -> None:
    first = _component(
        key='first',
        display_name='First',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.CENTER,
    )
    second = _component(
        key='second',
        display_name='Second',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.CENTER,
    )
    with pytest.raises(ToolManifestError, match='duplicate layout roles'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            sources=(_PI,),
            operational_scope=ToolScope.PLANT,
            body_sections=(
                first,
                second,
                _subcomponent(
                    component='first',
                    subcomponent='card',
                    display_name='Card',
                    scope=ToolScope.PLANT,
                    alarm=True,
                ),
                _subcomponent(
                    component='second',
                    subcomponent='card',
                    display_name='Card',
                    scope=ToolScope.PLANT,
                    alarm=True,
                ),
            ),
        )


def test_process_manifest_requires_at_least_one_card_per_component() -> None:
    center = _component(
        key='planta_molibdeno',
        display_name='Planta Molibdeno',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.CENTER,
    )
    with pytest.raises(ToolManifestError, match='requires at least one subcomponent'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            sources=(_PI,),
            operational_scope=ToolScope.PLANT,
            body_sections=(center,),
        )


def test_process_bottom_requires_exactly_one_card() -> None:
    center = _component(
        key='proceso',
        display_name='Proceso',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.CENTER,
    )
    bottom = _component(
        key='graficas',
        display_name='Gráficas',
        scope=ToolScope.PLANT,
        role=ProcessBodySection.BOTTOM,
    )
    with pytest.raises(ToolManifestError, match='bottom component requires exactly one'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            sources=(_PI,),
            operational_scope=ToolScope.PLANT,
            body_sections=(
                center,
                bottom,
                _subcomponent(
                    component='proceso',
                    subcomponent='principal',
                    display_name='Principal',
                    scope=ToolScope.PLANT,
                    alarm=True,
                ),
                _subcomponent(
                    component='graficas',
                    subcomponent='uno',
                    display_name='Uno',
                    scope=ToolScope.PLANT,
                ),
                _subcomponent(
                    component='graficas',
                    subcomponent='dos',
                    display_name='Dos',
                    scope=ToolScope.PLANT,
                ),
            ),
        )


def test_process_non_center_cards_cannot_be_alarm_targets() -> None:
    left = _component(
        key='aguas_arriba',
        display_name='Aguas Arriba',
        scope=ToolScope.MINE,
        role=ProcessBodySection.LEFT,
    )
    center = _component(
        key='proceso_chancado',
        display_name='Proceso Chancado',
        scope=ToolScope.MINE,
        role=ProcessBodySection.CENTER,
    )
    with pytest.raises(ToolManifestError, match='non-center subcomponents cannot declare targets'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            sources=(_PI,),
            operational_scope=ToolScope.MINE,
            body_sections=(
                left,
                center,
                _subcomponent(
                    component='aguas_arriba',
                    subcomponent='ch1',
                    display_name='CH1',
                    scope=ToolScope.MINE,
                    alarm=True,
                ),
                _subcomponent(
                    component='proceso_chancado',
                    subcomponent='principal',
                    display_name='Principal',
                    scope=ToolScope.MINE,
                    alarm=True,
                ),
            ),
        )
