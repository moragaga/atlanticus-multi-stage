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
from ada.features.dashboard import (
    ComponentProjectionDefinition,
    ComponentRendererDefinition,
    ComponentRendererRegistry,
    DashboardDefinition,
    DashboardDefinitionError,
    DashboardToolConfiguration,
)


def _renderer(bundle: object) -> object:
    return bundle


def _process_manifest():
    return build_process_manifest(
        tool_key='process_reference',
        display_name='Process Reference',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=60),),
        operational_scope=ToolScope.PLANT,
        body_sections=(
            ToolSection(
                key='center_process',
                display_name='Proceso Central',
                kind=ToolSectionKind.COMPONENT,
                scope=ToolScope.PLANT,
                parent_key='body',
                targets=(ToolTarget.KPI, ToolTarget.ALARM),
                layout_role=ProcessBodySection.CENTER,
            ),
            ToolSection(
                component='center_process',
                subcomponent='main',
                display_name='Principal',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=ToolScope.PLANT,
                targets=(ToolTarget.ALARM,),
            ),
            ToolSection(
                key='right_process',
                display_name='Proceso Derecho',
                kind=ToolSectionKind.COMPONENT,
                scope=ToolScope.PLANT,
                parent_key='body',
                targets=(ToolTarget.KPI,),
                layout_role=ProcessBodySection.RIGHT,
            ),
            ToolSection(
                component='right_process',
                subcomponent='main',
                display_name='Principal',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=ToolScope.PLANT,
            ),
        ),
    )


def test_dashboard_definition_discovers_only_real_io_body_components() -> None:
    definition = DashboardDefinition.build(
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
        configuration=DashboardToolConfiguration(),
        renderers=ComponentRendererRegistry(),
    )

    assert tuple(component.section.key for component in definition.components) == (
        'general_mina',
        'carguio',
        'transporte',
        'chancado_stmg',
        'stockpile_chacay',
        'molienda',
        'flotacion',
        'transporte_fluidos',
        'puerto',
    )
    assert 'carguio_transporte' not in tuple(
        component.section.key for component in definition.components
    )


def test_dashboard_definition_supports_generic_process_body_components() -> None:
    definition = DashboardDefinition.build(
        manifest=_process_manifest(),
        configuration=DashboardToolConfiguration(),
        renderers=ComponentRendererRegistry(),
    )

    assert tuple(component.section.key for component in definition.components) == (
        'center_process',
        'right_process',
    )


def test_declared_component_without_renderer_is_construction_and_needs_no_callback() -> None:
    definition = DashboardDefinition.build(
        manifest=_process_manifest(),
        configuration=DashboardToolConfiguration(
            components=(ComponentProjectionDefinition(component_key='center_process', data=True),)
        ),
        renderers=ComponentRendererRegistry(),
    )

    component = definition.component('center_process')

    assert component.construction is True
    assert component.callback_required is False


def test_renderer_and_projection_make_component_ready_for_automatic_callback_wiring() -> None:
    definition = DashboardDefinition.build(
        manifest=_process_manifest(),
        configuration=DashboardToolConfiguration(
            components=(ComponentProjectionDefinition(component_key='center_process', data=True),)
        ),
        renderers=ComponentRendererRegistry(
            definitions=(
                ComponentRendererDefinition(component_key='center_process', renderer=_renderer),
            )
        ),
    )

    component = definition.component('center_process')

    assert component.construction is False
    assert component.callback_required is True


def test_renderer_for_unknown_component_fails_at_dashboard_definition_startup() -> None:
    with pytest.raises(DashboardDefinitionError, match='renderer references unknown component'):
        DashboardDefinition.build(
            manifest=_process_manifest(),
            configuration=DashboardToolConfiguration(),
            renderers=ComponentRendererRegistry(
                definitions=(
                    ComponentRendererDefinition(component_key='unknown', renderer=_renderer),
                )
            ),
        )


def test_projection_for_unknown_component_fails_at_dashboard_definition_startup() -> None:
    with pytest.raises(DashboardDefinitionError, match='projection references unknown component'):
        DashboardDefinition.build(
            manifest=_process_manifest(),
            configuration=DashboardToolConfiguration(
                components=(ComponentProjectionDefinition(component_key='unknown', data=True),)
            ),
            renderers=ComponentRendererRegistry(),
        )
