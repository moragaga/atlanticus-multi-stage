from __future__ import annotations

from dataclasses import dataclass

from dash import html
from dash.development.base_component import Component

from ada.configuration.tools import ToolConfigurationProjection
from ada.contracts.tool_manifest import ProcessBodySection, ToolManifest, ToolSectionKind
from ada.features.alarms import (
    AlarmPresentationInteraction,
    alarm_geometry_scope_attributes,
    alarm_presentation_scope_attributes,
    build_alarm_dashboard_route_layer,
    build_process_alarm_baseline,
)
from ada.features.dashboard import (
    ComponentRendererRegistry,
    DashboardDefinition,
    DashboardMount,
    DashboardPollingSettings,
    DashboardToolConfiguration,
    build_dashboard_mount,
)
from ada.runtime.component_stores import (
    RuntimeComponentStoreMount,
    build_runtime_component_store_mount,
    build_runtime_component_store_registry,
)
from ada.ui.components.component_card import build_component_card
from ada.ui.layouts.process import build_process_layout
from ada.ui.shell.header import HeaderState
from ada.ui.shell.operational import build_ada_operational_shell
from ada.ui.shell.time_status import TimeStatusState

from .errors import ProcessCompositionError


@dataclass(frozen=True, slots=True)
class ProcessToolComposition:
    dashboard: DashboardDefinition
    mount: DashboardMount
    projection: ToolConfigurationProjection | None = None
    runtime_store_mount: RuntimeComponentStoreMount | None = None

    @property
    def manifest(self) -> ToolManifest:
        return self.dashboard.manifest

    def build_body(self, *, layout_id: str | None = None) -> html.Div:
        content = {
            component.key: _build_component_cards(
                self.manifest,
                component_key=component.key,
                mount=self.mount,
                projection=self.projection,
            )
            for component in self.manifest.children('body')
        }
        return build_process_layout(
            self.manifest,
            component_content=content,
            component_wrapper_ids=_component_wrapper_ids(self.projection),
            layout_id=layout_id,
            class_name='ada-process-tool__layout',
        )

    def build_tool(
        self,
        *,
        header_state: HeaderState,
        alarm_management_slot: Component | None = None,
        alarm_status_slot: Component | None = None,
        time_status_state: TimeStatusState | None = None,
        alarm_content: Component | None = None,
        desktop_navigation_trigger: Component | None = None,
        mobile_navigation_trigger: Component | None = None,
        layout_id: str | None = None,
        class_name: str | None = None,
        alarm_trace_dwell_ms: int = 15_000,
        alarm_interaction: AlarmPresentationInteraction = AlarmPresentationInteraction.INTERACTIVE,
    ) -> html.Div:
        _validate_header_state(self.manifest, header_state)
        _validate_time_status_state(self.manifest, time_status_state)
        return build_ada_operational_shell(
            self.manifest,
            header_state=header_state,
            body_content=self.build_body(layout_id=layout_id),
            alarm_children=_build_alarm_children(alarm_content),
            alarm_management_slot=alarm_management_slot,
            alarm_status_slot=alarm_status_slot,
            time_status_state=time_status_state,
            desktop_navigation_trigger=desktop_navigation_trigger,
            mobile_navigation_trigger=mobile_navigation_trigger,
            runtime_hosts=_runtime_hosts(self.mount, self.runtime_store_mount),
            runtime_component_wrapper_ids=_component_wrapper_ids(self.projection),
            shell_class_name=_join_classes('ada-process-tool', class_name),
            time_status_class_name='ada-process-tool__time-status',
            alarm_surface_class_name='ada-process-tool__alarm-surface',
            body_class_name='ada-process-tool__body',
            shell_attributes={
                'data-ada-process-tool': self.manifest.tool_key,
                **alarm_geometry_scope_attributes(),
                **alarm_presentation_scope_attributes(
                    trace_dwell_ms=alarm_trace_dwell_ms,
                    interaction=alarm_interaction,
                ),
            },
            alarm_surface_attributes={
                'data-ada-process-alarm-surface': 'true',
            },
        )


def create_process_tool_composition(
    manifest: ToolManifest,
    *,
    projection: ToolConfigurationProjection | None = None,
    dashboard_configuration: DashboardToolConfiguration | None = None,
    renderers: ComponentRendererRegistry | None = None,
    polling: DashboardPollingSettings | None = None,
    dashboard_key: str | None = None,
) -> ProcessToolComposition:
    _validate_process_manifest(manifest)
    _validate_projection(manifest, projection)
    dashboard = DashboardDefinition.build(
        manifest=manifest,
        configuration=dashboard_configuration or DashboardToolConfiguration(),
        renderers=renderers or ComponentRendererRegistry(),
        polling=polling,
    )
    runtime_store_mount = _build_runtime_store_mount(projection)
    return ProcessToolComposition(
        dashboard=dashboard,
        mount=build_dashboard_mount(dashboard, dashboard_key=dashboard_key),
        projection=projection,
        runtime_store_mount=runtime_store_mount,
    )


def _build_component_cards(
    manifest: ToolManifest,
    *,
    component_key: str,
    mount: DashboardMount,
    projection: ToolConfigurationProjection | None,
) -> html.Div:
    cards = []
    for section in manifest.children(component_key):
        if section.subcomponent is None:
            continue
        slot = mount.slot(component_key, section.subcomponent)
        cards.append(
            build_component_card(
                manifest,
                component=component_key,
                subcomponent=section.subcomponent,
                content=slot.content,
                label=section.display_name,
                overlay=slot.overlay,
                class_name='ada-process-tool__card',
                wrapper_id=_subcomponent_wrapper_id(
                    projection,
                    component_key=component_key,
                    subcomponent_key=section.subcomponent,
                ),
            )
        )
    return html.Div(cards, className='ada-process-tool__component-cards')


def _build_alarm_children(content: Component | None) -> tuple[Component, ...]:
    children: list[Component] = []
    if content is not None:
        children.append(html.Div(content, className='ada-process-tool__alarm-content'))
    children.extend(
        (
            build_alarm_dashboard_route_layer(),
            build_process_alarm_baseline(),
        )
    )
    return tuple(children)


def _build_runtime_store_mount(
    projection: ToolConfigurationProjection | None,
) -> RuntimeComponentStoreMount | None:
    if projection is None:
        return None
    return build_runtime_component_store_mount(build_runtime_component_store_registry(projection))


def _runtime_hosts(
    dashboard_mount: DashboardMount,
    runtime_store_mount: RuntimeComponentStoreMount | None,
) -> tuple[Component, ...]:
    hosts: list[Component] = [dashboard_mount.runtime_host()]
    if runtime_store_mount is not None:
        hosts.append(runtime_store_mount.runtime_host())
    return tuple(hosts)


def _component_wrapper_ids(
    projection: ToolConfigurationProjection | None,
) -> dict[str, str]:
    if projection is None:
        return {}
    return {binding.component_key: binding.wrapper_id for binding in projection.runtime.components}


def _subcomponent_wrapper_id(
    projection: ToolConfigurationProjection | None,
    *,
    component_key: str,
    subcomponent_key: str,
) -> str | None:
    if projection is None:
        return None
    return projection.runtime.subcomponent(
        component_key=component_key,
        subcomponent_key=subcomponent_key,
    ).wrapper_id


def _validate_projection(
    manifest: ToolManifest,
    projection: ToolConfigurationProjection | None,
) -> None:
    if projection is None:
        return
    if not isinstance(projection, ToolConfigurationProjection):
        raise ProcessCompositionError(f'Invalid process tool projection: {projection!r}')
    if projection.manifest.tool_key != manifest.tool_key:
        raise ProcessCompositionError('Tool projection tool key does not match process manifest')
    if projection.manifest != manifest:
        raise ProcessCompositionError('Tool projection manifest does not match process manifest')


def _validate_process_manifest(manifest: ToolManifest) -> None:
    if not isinstance(manifest, ToolManifest):
        raise ProcessCompositionError(f'Invalid process tool manifest: {manifest!r}')
    body = manifest.section('body')
    if body.kind is not ToolSectionKind.REGION:
        raise ProcessCompositionError('Process tool body must be a region')
    components = manifest.children('body')
    if any(
        component.kind is not ToolSectionKind.COMPONENT or component.layout_role is None
        for component in components
    ):
        raise ProcessCompositionError('Process tool body must contain only layout components')
    if not any(component.layout_role is ProcessBodySection.CENTER for component in components):
        raise ProcessCompositionError('Process tool requires the center layout role')


def _validate_header_state(manifest: ToolManifest, state: HeaderState) -> None:
    if state.tool_key != manifest.tool_key:
        raise ProcessCompositionError('Header state tool key does not match process manifest')


def _validate_time_status_state(
    manifest: ToolManifest,
    state: TimeStatusState | None,
) -> None:
    if state is not None and state.tool_key != manifest.tool_key:
        raise ProcessCompositionError('Time status tool key does not match process manifest')


def _join_classes(*values: str | None) -> str:
    return ' '.join(value.strip() for value in values if value and value.strip())
