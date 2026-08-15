from dash import html

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
    DashboardPollingSettings,
    DashboardToolConfiguration,
    build_dashboard_mount,
)


def _props(component):
    return component.to_plotly_json()['props']


def _manifest():
    return build_process_manifest(
        tool_key='mount_reference',
        display_name='Mount Reference',
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


def _renderer(_bundle):
    return {'main': html.Div('ok')}


def test_mount_creates_slots_for_existing_cards_without_replacing_component_layout() -> None:
    definition = DashboardDefinition.build(
        manifest=_manifest(),
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
                    renderer=_renderer,
                ),
            )
        ),
    )

    mount = build_dashboard_mount(definition)

    assert set(mount.subcomponent_slots) == {
        ('center_process', 'main'),
        ('right_process', 'main'),
    }
    assert not hasattr(mount, 'component_content')
    assert len(mount.stores) == 3
    assert _props(mount.slot('center_process', 'main').content)['id'].endswith('--content')
    construction_overlay = _props(mount.slot('right_process', 'main').overlay)['children']
    assert construction_overlay is not None


def test_mount_keeps_renderer_without_projection_in_construction_without_stores() -> None:
    definition = DashboardDefinition.build(
        manifest=_manifest(),
        configuration=DashboardToolConfiguration(),
        renderers=ComponentRendererRegistry(
            definitions=(
                ComponentRendererDefinition(
                    component_key='center_process',
                    renderer=_renderer,
                ),
            )
        ),
    )

    mount = build_dashboard_mount(definition)

    assert mount.stores == ()
    assert _props(mount.slot('center_process', 'main').overlay)['children'] is not None


def test_mount_uses_explicit_dashboard_key_for_generated_store_and_slot_ids() -> None:
    definition = DashboardDefinition.build(
        manifest=_manifest(),
        configuration=DashboardToolConfiguration(
            components=(ComponentProjectionDefinition(component_key='center_process', data=True),)
        ),
        renderers=ComponentRendererRegistry(
            definitions=(
                ComponentRendererDefinition(component_key='center_process', renderer=_renderer),
            )
        ),
    )

    mount = build_dashboard_mount(definition, dashboard_key='instance-a')
    store_ids = {_props(store)['id'] for store in mount.stores}
    slot_id = _props(mount.slot('center_process', 'main').content)['id']

    assert mount.dashboard_key == 'instance-a'
    assert all(value.startswith('ada-dashboard--instance-a--') for value in store_ids)
    assert slot_id.startswith('ada-dashboard--instance-a--')


def test_mount_adds_one_shared_interval_and_revision_store_per_active_channel() -> None:
    definition = DashboardDefinition.build(
        manifest=_manifest(),
        configuration=DashboardToolConfiguration(
            components=(ComponentProjectionDefinition(component_key='center_process', data=True),)
        ),
        renderers=ComponentRendererRegistry(
            definitions=(
                ComponentRendererDefinition(component_key='center_process', renderer=_renderer),
            )
        ),
        polling=DashboardPollingSettings(interval_seconds=5),
    )

    mount = build_dashboard_mount(definition)
    store_ids = {_props(store)['id'] for store in mount.stores}

    assert len(mount.intervals) == 1
    assert _props(mount.intervals[0])['interval'] == 5000
    assert any(value.endswith('--data--revision') for value in store_ids)
    assert any(value.endswith('--status--revision') for value in store_ids)
    assert not any(value.endswith('--time-series--revision') for value in store_ids)
    host_children = _props(mount.store_host())['children']
    assert len(host_children) == len(mount.stores) + 1
