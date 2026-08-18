import pytest

from ada.configuration.tools import (
    ToolComponentConfiguration,
    ToolConfiguration,
    ToolConfigurationCatalog,
    ToolConfigurationKind,
    ToolSourceConfiguration,
    ToolSubcomponentConfiguration,
    build_tool_manifest,
    build_tool_manifest_registry,
    integrated_operations_configuration_from_manifest,
)
from ada.configuration.tools.errors import ToolConfigurationValidationError
from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ProcessBodySection,
    ToolScope,
    ToolSourceKey,
    ToolTarget,
)


def test_integrated_operations_migration_rebuilds_current_manifest_exactly() -> None:
    configuration = integrated_operations_configuration_from_manifest(
        INTEGRATED_OPERATIONS_MANIFEST
    )

    assert build_tool_manifest(configuration) == INTEGRATED_OPERATIONS_MANIFEST


def test_integrated_operations_derived_targets_match_ada_semantics() -> None:
    manifest = build_tool_manifest(
        integrated_operations_configuration_from_manifest(INTEGRATED_OPERATIONS_MANIFEST)
    )

    assert manifest.section('global_indicators').accepts(ToolTarget.KPI)
    assert not manifest.section('global_indicators').accepts(ToolTarget.ALARM)
    assert manifest.section('time_status').accepts(ToolTarget.KPI)
    assert not manifest.section('time_status').accepts(ToolTarget.ALARM)
    assert manifest.section('flotacion').accepts(ToolTarget.KPI)
    assert manifest.section('flotacion').accepts(ToolTarget.ALARM)
    assert not manifest.section('flotacion_selectiva').accepts(ToolTarget.KPI)
    assert manifest.section('flotacion_selectiva').accepts(ToolTarget.ALARM)


def test_tool_can_project_with_dispatch_as_its_only_source() -> None:
    configuration = ToolConfiguration(
        tool_key='dispatch_process',
        display_name='Dispatch Process',
        kind=ToolConfigurationKind.PROCESS,
        operational_scope=ToolScope.MINE,
        sources=(ToolSourceConfiguration(ToolSourceKey.DISPATCH, 600),),
        components=(
            ToolComponentConfiguration(
                key='dispatch',
                display_name='Dispatch',
                layout_role=ProcessBodySection.CENTER,
                subcomponents=(
                    ToolSubcomponentConfiguration(
                        key='estado',
                        display_name='Estado',
                    ),
                ),
            ),
        ),
    )

    manifest = build_tool_manifest(configuration)

    assert manifest.has_source(ToolSourceKey.DISPATCH)
    assert not manifest.has_source(ToolSourceKey.PI)


def test_draft_can_be_incomplete_but_projection_is_strict() -> None:
    draft = ToolConfiguration(
        tool_key='flotacion',
        display_name='Flotación',
        kind=ToolConfigurationKind.PROCESS,
    )

    with pytest.raises(ToolConfigurationValidationError, match='mine or plant'):
        build_tool_manifest(draft)


def test_process_derives_center_and_context_targets() -> None:
    configuration = ToolConfiguration(
        tool_key='flotacion_colectiva',
        display_name='Flotación Colectiva',
        kind=ToolConfigurationKind.PROCESS,
        operational_scope=ToolScope.PLANT,
        sources=(ToolSourceConfiguration(ToolSourceKey.PI, 300),),
        components=(
            ToolComponentConfiguration(
                key='molienda',
                display_name='Molienda',
                layout_role=ProcessBodySection.LEFT,
                subcomponents=(
                    ToolSubcomponentConfiguration(key='molienda', display_name='Molienda'),
                ),
            ),
            ToolComponentConfiguration(
                key='flotacion',
                display_name='Flotación',
                layout_role=ProcessBodySection.CENTER,
                subcomponents=(
                    ToolSubcomponentConfiguration(key='colectiva', display_name='Colectiva'),
                    ToolSubcomponentConfiguration(key='selectiva', display_name='Selectiva'),
                ),
            ),
            ToolComponentConfiguration(
                key='transporte_fluidos',
                display_name='Transporte de Fluidos',
                layout_role=ProcessBodySection.RIGHT,
                subcomponents=(
                    ToolSubcomponentConfiguration(key='str', display_name='STR'),
                ),
            ),
        ),
    )

    manifest = build_tool_manifest(configuration)

    assert manifest.section('flotacion').accepts(ToolTarget.KPI)
    assert manifest.section('flotacion').accepts(ToolTarget.ALARM)
    assert manifest.section('flotacion_colectiva').accepts(ToolTarget.ALARM)
    assert not manifest.section('flotacion_colectiva').accepts(ToolTarget.KPI)
    assert manifest.section('molienda').accepts(ToolTarget.KPI)
    assert not manifest.section('molienda').accepts(ToolTarget.ALARM)
    assert not manifest.section('molienda_molienda').targets
    assert manifest.section('global_indicators').targets == frozenset({ToolTarget.KPI})
    assert manifest.section('time_status').targets == frozenset({ToolTarget.KPI})


def test_registry_preserves_catalog_order() -> None:
    integrated = integrated_operations_configuration_from_manifest(
        INTEGRATED_OPERATIONS_MANIFEST
    )
    process = ToolConfiguration(
        tool_key='flotacion',
        display_name='Flotación',
        kind=ToolConfigurationKind.PROCESS,
        operational_scope=ToolScope.PLANT,
        sources=(ToolSourceConfiguration(ToolSourceKey.PI, 300),),
        components=(
            ToolComponentConfiguration(
                key='flotacion',
                display_name='Flotación',
                layout_role=ProcessBodySection.CENTER,
                subcomponents=(
                    ToolSubcomponentConfiguration(key='colectiva', display_name='Colectiva'),
                ),
            ),
        ),
    )

    registry = build_tool_manifest_registry(ToolConfigurationCatalog((integrated, process)))

    assert [manifest.tool_key for manifest in registry.manifests] == [
        'integrated_operations',
        'flotacion',
    ]
