from importlib.resources import files

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
from ada.features.dashboard import (
    ADA_DASHBOARD_ASSET_LAYER,
    ComponentRendererRegistry,
    DashboardDefinition,
    DashboardToolConfiguration,
    create_ada_dashboard_module,
)


def _definition() -> DashboardDefinition:
    manifest = build_process_manifest(
        tool_key='dashboard_assets',
        display_name='Dashboard Assets',
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
    return DashboardDefinition.build(
        manifest=manifest,
        configuration=DashboardToolConfiguration(),
        renderers=ComponentRendererRegistry(),
    )


def test_dashboard_content_slot_assets_are_packaged() -> None:
    resources = files('ada.features.dashboard.ui').joinpath('resources', 'css')
    css_list = resources.joinpath('css.list').read_text().splitlines()
    packaged = sorted(
        item.name for item in resources.iterdir() if item.is_file() and item.name != 'css.list'
    )

    assert css_list == ['10-content-slot.css']
    assert packaged == css_list
    css = resources.joinpath(css_list[0]).read_text()
    assert '.ada-dashboard-content-slot' in css
    assert 'height: 100%;' in css
    assert 'overflow: hidden;' in css
    assert '.js-plotly-plot' in css
    assert 'height: 100% !important;' in css
    assert 'max-height: 100% !important;' in css


def test_dashboard_module_declares_content_slot_asset_layer() -> None:
    module = create_ada_dashboard_module(_definition())

    assert module.asset_layers == (ADA_DASHBOARD_ASSET_LAYER,)
    assert ADA_DASHBOARD_ASSET_LAYER.load_order == 245
