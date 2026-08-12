import pytest

from ada.contracts.tool_manifest import (
    ProcessBodySection,
    ToolManifestError,
    ToolTarget,
    build_process_manifest,
)


def test_process_manifest_accepts_center_only() -> None:
    manifest = build_process_manifest(
        tool_key='flotacion_selectiva',
        display_name='Flotación Selectiva',
        body_sections=(ProcessBodySection.CENTER,),
    )

    assert [section.key for section in manifest.children('body')] == ['center']
    assert manifest.require_target('center', ToolTarget.ALARM).key == 'center'
    assert manifest.require_target('center', ToolTarget.KPI).key == 'center'


def test_process_manifest_allows_kpis_in_other_visual_sections_but_alarms_only_in_center() -> None:
    manifest = build_process_manifest(
        tool_key='molienda',
        display_name='Molienda',
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


def test_process_manifest_requires_center() -> None:
    with pytest.raises(ToolManifestError, match='requires the center section'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            body_sections=(ProcessBodySection.LEFT,),
        )


def test_process_manifest_rejects_duplicate_body_sections() -> None:
    with pytest.raises(ToolManifestError, match='duplicate body sections'):
        build_process_manifest(
            tool_key='invalid_process',
            display_name='Invalid Process',
            body_sections=(ProcessBodySection.CENTER, ProcessBodySection.CENTER),
        )
