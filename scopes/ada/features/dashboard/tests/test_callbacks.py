from dash import Dash

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
    ComponentProjectionDefinition,
    ComponentRendererDefinition,
    ComponentRendererRegistry,
    DashboardDefinition,
    DashboardToolConfiguration,
    create_ada_dashboard_module,
    register_dashboard_callbacks,
)


def _definition():
    manifest = build_process_manifest(
        tool_key='callback_reference',
        display_name='Callback Reference',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=60),),
        operational_scope=ToolScope.PLANT,
        body_sections=(
            ToolSection(
                key='center_process',
                display_name='Centro',
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
                display_name='Derecha',
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
    return DashboardDefinition.build(
        manifest=manifest,
        configuration=DashboardToolConfiguration(
            components=(
                ComponentProjectionDefinition(component_key='center_process', data=True),
                ComponentProjectionDefinition(component_key='right_process', data=True),
            )
        ),
        renderers=ComponentRendererRegistry(
            definitions=(
                ComponentRendererDefinition(
                    component_key='center_process',
                    renderer=lambda _bundle: {'main': 'ok'},
                ),
            )
        ),
    )


def test_callback_factory_targets_subcomponent_slots_only_for_active_component() -> None:
    app = Dash(__name__)

    register_dashboard_callbacks(app, _definition())

    assert len(app.callback_map) == 2
    callback_keys = tuple(app.callback_map)
    assert any('--content.children' in key for key in callback_keys)
    assert any('--overlay.children' in key for key in callback_keys)
    assert not any('right_process' in key for key in callback_keys)


def test_dashboard_web_module_exposes_automatic_callback_registrar() -> None:
    module = create_ada_dashboard_module(_definition())

    assert module.name == 'ada-dashboard'
    assert module.register_callbacks is not None


def test_dashboard_web_module_requires_reader_when_polling_is_enabled() -> None:
    import pytest

    from ada.features.dashboard import DashboardDefinitionError, DashboardPollingSettings

    base = _definition()
    definition = DashboardDefinition(
        manifest=base.manifest,
        configuration=base.configuration,
        components=base.components,
        polling=DashboardPollingSettings(interval_seconds=5),
    )

    with pytest.raises(DashboardDefinitionError, match='requires SharedSnapshotReader'):
        create_ada_dashboard_module(definition)
