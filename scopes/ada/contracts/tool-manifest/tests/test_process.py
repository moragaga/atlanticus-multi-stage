import pytest

from ada.contracts.tool_manifest import (
    ProcessBodySection,
    ToolManifestError,
    ToolScope,
    ToolSource,
    ToolSourceKey,
    ToolTarget,
    build_process_manifest,
)

_PI = ToolSource(ToolSourceKey.PI, stale_after_seconds=300)


def test_process_manifest_accepts_center_only_and_plant_scope() -> None:
    manifest = build_process_manifest(
        tool_key='flotacion_selectiva',
        display_name='Flotación Selectiva',
        sources=(_PI,),
        operational_scope=ToolScope.PLANT,
        body_sections=(ProcessBodySection.CENTER,),
    )

    assert [section.key for section in manifest.children('body')] == ['center']
    assert manifest.source(ToolSourceKey.PI) is _PI
    assert not manifest.has_source(ToolSourceKey.DISPATCH)
    assert manifest.section('global_indicators').scope is ToolScope.PLANT
    assert manifest.section('alarm_management').scope is ToolScope.PLANT
    assert manifest.section('alarm_status').scope is ToolScope.GLOBAL
    assert manifest.require_target('center', ToolTarget.ALARM).scope is ToolScope.PLANT


def test_process_manifest_accepts_mine_scope() -> None:
    manifest = build_process_manifest(
        tool_key='chancado_stmg',
        display_name='Chancado-STMG',
        sources=(_PI,),
        operational_scope=ToolScope.MINE,
        body_sections=(ProcessBodySection.CENTER,),
    )

    assert manifest.section('global_indicators').scope is ToolScope.MINE
    assert manifest.section('alarm_management').scope is ToolScope.MINE
    assert manifest.section('center').scope is ToolScope.MINE


def test_process_manifest_allows_kpis_in_other_visual_sections_but_alarms_only_in_center() -> None:
    manifest = build_process_manifest(
        tool_key='molienda',
        display_name='Molienda',
        sources=(_PI,),
        operational_scope=ToolScope.PLANT,
        body_sections=(
            ProcessBodySection.LEFT,
            ProcessBodySection.CENTER,
            ProcessBodySection.RIGHT,
            ProcessBodySection.BOTTOM,
        ),
    )

    kpi_keys = {section.key for section in manifest.sections_for_target(ToolTarget.KPI)}
    alarm_keys = {section.key for section in manifest.sections_for_target(ToolTarget.ALARM)}

    assert {'global_indicators', 'left', 'center', 'right', 'bottom'} <= kpi_keys
    assert alarm_keys == {'center'}


def test_process_manifest_rejects_global_operational_scope() -> None:
    with pytest.raises(ToolManifestError, match='must be mine or plant'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            sources=(_PI,),
            operational_scope=ToolScope.GLOBAL,
            body_sections=(ProcessBodySection.CENTER,),
        )


def test_process_manifest_requires_center() -> None:
    with pytest.raises(ToolManifestError, match='requires the center section'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            sources=(_PI,),
            operational_scope=ToolScope.MINE,
            body_sections=(ProcessBodySection.LEFT,),
        )


def test_process_manifest_rejects_duplicate_body_sections() -> None:
    with pytest.raises(ToolManifestError, match='duplicate body sections'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            sources=(_PI,),
            operational_scope=ToolScope.MINE,
            body_sections=(ProcessBodySection.CENTER, ProcessBodySection.CENTER),
        )
