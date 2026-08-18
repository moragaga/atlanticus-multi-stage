from ada.compositions.process import (
    ADA_PROCESS_COMPOSITION_ASSET_LAYER,
    create_process_tool_composition,
    create_process_tool_modules,
)
from ada.contracts.tool_manifest import (
    ProcessBodySection,
    ToolScope,
    ToolSection,
    ToolSectionKind,
    ToolSource,
    ToolSourceKey,
    ToolTarget,
    build_process_manifest,
)


def _composition():
    manifest = build_process_manifest(
        tool_key='process_module_reference',
        display_name='Process Module Reference',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=60),),
        operational_scope=ToolScope.PLANT,
        body_sections=(
            ToolSection(
                key='center',
                display_name='Center',
                kind=ToolSectionKind.COMPONENT,
                scope=ToolScope.PLANT,
                parent_key='body',
                targets=(ToolTarget.KPI, ToolTarget.ALARM),
                layout_role=ProcessBodySection.CENTER,
            ),
            ToolSection(
                component='center',
                subcomponent='main',
                display_name='Main',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=ToolScope.PLANT,
                targets=(ToolTarget.ALARM,),
            ),
        ),
    )
    return create_process_tool_composition(manifest)


def test_process_modules_assemble_capabilities_without_application_code() -> None:
    modules = create_process_tool_modules(_composition())
    names = tuple(module.name for module in modules)

    assert names == (
        'ada-ui',
        'ada-state-wrapper',
        'ada-global-indicator',
        'ada-component-container',
        'ada-component-card',
        'ada-process-layout',
        'ada-alarms',
        'ada-header',
        'ada-time-status',
        'ada-dashboard',
        'ada-process-composition',
    )
    assert modules[-1].asset_layers == (ADA_PROCESS_COMPOSITION_ASSET_LAYER,)
    assert ADA_PROCESS_COMPOSITION_ASSET_LAYER.load_order == 280
