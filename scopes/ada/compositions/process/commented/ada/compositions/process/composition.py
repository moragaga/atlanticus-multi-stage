# Espejo comentado: composition genérica Process; la lógica ejecutable es idéntica al productivo.
from __future__ import annotations

from dataclasses import dataclass

from dash import html
from dash.development.base_component import Component

from ada.contracts.tool_manifest import ProcessBodySection, ToolManifest, ToolSectionKind
from ada.features.alarms import (
    AlarmPresentationInteraction,
    alarm_geometry_scope_attributes,
    alarm_presentation_scope_attributes,
    build_alarm_dashboard_route_layer,
    build_process_alarm_baseline,
)
from ada.features.alarms.management_summary import build_alarm_management_summary
from ada.features.alarms.notifications import build_alarm_status
from ada.features.dashboard import (
    ComponentRendererRegistry,
    DashboardDefinition,
    DashboardMount,
    DashboardPollingSettings,
    DashboardToolConfiguration,
    build_dashboard_mount,
)
from ada.ui.components.component_card import build_component_card
from ada.ui.components.state_wrapper import ComponentCover, build_state_wrapper
from ada.ui.framework.core import build_ready_scope
from ada.ui.layouts.process import build_process_layout
from ada.ui.shell.header import HeaderState, build_ada_header
from ada.ui.shell.time_status import TimeStatusState, build_ada_time_status

from .errors import ProcessCompositionError


# La composition conserva una única definición Dashboard y su mount; no duplica capabilities.
@dataclass(frozen=True, slots=True)
class ProcessToolComposition:
    dashboard: DashboardDefinition
    mount: DashboardMount

    @property
    def manifest(self) -> ToolManifest:
        return self.dashboard.manifest

    # El body se deriva completamente del manifest y de los slots que Dashboard ya declaró.
    def build_body(self, *, layout_id: str | None = None) -> html.Div:
        content = {
            component.key: _build_component_cards(
                self.manifest,
                component_key=component.key,
                mount=self.mount,
            )
            for component in self.manifest.children('body')
        }
        return build_process_layout(
            self.manifest,
            component_content=content,
            layout_id=layout_id,
            class_name='ada-process-tool__layout',
        )

    # Esta frontera ensambla la herramienta completa: Header, TimeStatus, alarmas, body y runtime.
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
        children: list[Component] = [
            build_ada_header(
                header_state,
                alarm_management_slot=(
                    alarm_management_slot
                    if alarm_management_slot is not None
                    else build_alarm_management_summary(
                        None,
                        cover=ComponentCover.construction(),
                    )
                ),
                alarm_status_slot=(
                    alarm_status_slot
                    if alarm_status_slot is not None
                    else build_alarm_status(
                        None,
                        cover=ComponentCover.construction(),
                    )
                ),
                desktop_navigation_trigger=desktop_navigation_trigger,
                mobile_navigation_trigger=mobile_navigation_trigger,
            )
        ]
        children.append(
            html.Div(
                _build_time_status(self.manifest, time_status_state),
                className='ada-process-tool__time-status',
            )
        )
        children.extend(
            (
                _build_alarm_surface(alarm_content),
                html.Main(
                    self.build_body(layout_id=layout_id),
                    className='ada-process-tool__body',
                ),
                self.mount.runtime_host(),
            )
        )
        return build_ready_scope(
            content=html.Div(
                children,
                className=_join_classes('ada-process-tool', class_name),
                **{
                    'data-ada-process-tool': self.manifest.tool_key,
                    **alarm_geometry_scope_attributes(),
                    **alarm_presentation_scope_attributes(
                        trace_dwell_ms=alarm_trace_dwell_ms,
                        interaction=alarm_interaction,
                    ),
                },
            ),
            required=(
                'global-indicators',
                'alarm-management',
                'alarm-status',
                'time-status',
            ),
        )


# Factory pública: el consumidor aporta contratos/configuración, no wiring interno.
def create_process_tool_composition(
    manifest: ToolManifest,
    *,
    dashboard_configuration: DashboardToolConfiguration | None = None,
    renderers: ComponentRendererRegistry | None = None,
    polling: DashboardPollingSettings | None = None,
    dashboard_key: str | None = None,
) -> ProcessToolComposition:
    _validate_process_manifest(manifest)
    dashboard = DashboardDefinition.build(
        manifest=manifest,
        configuration=dashboard_configuration or DashboardToolConfiguration(),
        renderers=renderers or ComponentRendererRegistry(),
        polling=polling,
    )
    return ProcessToolComposition(
        dashboard=dashboard,
        mount=build_dashboard_mount(dashboard, dashboard_key=dashboard_key),
    )


# Cada subcomponente manifestado obtiene una ComponentCard estable y un slot Dashboard confinado.
def _build_component_cards(
    manifest: ToolManifest,
    *,
    component_key: str,
    mount: DashboardMount,
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
            )
        )
    return html.Div(cards, className='ada-process-tool__component-cards')


# Mientras una herramienta no tenga estado temporal real, la superficie existe en CONSTRUCTION.
def _build_time_status(
    manifest: ToolManifest,
    state: TimeStatusState | None,
) -> Component:
    if state is None:
        return build_state_wrapper(
            cover=ComponentCover.construction(),
            ready_name='time-status',
        )
    _validate_time_status_state(manifest, state)
    return build_state_wrapper(
        content=build_ada_time_status(state),
        ready_name='time-status',
    )


# La composition monta el route layer y baseline existentes; no reimplementa el engine de alarmas.
def _build_alarm_surface(content: Component | None) -> html.Section:
    children: list[Component] = []
    if content is not None:
        children.append(html.Div(content, className='ada-process-tool__alarm-content'))
    children.extend(
        (
            build_alarm_dashboard_route_layer(),
            build_process_alarm_baseline(),
        )
    )
    return html.Section(
        children,
        className='ada-process-tool__alarm-surface',
        **{'data-ada-process-alarm-surface': 'true'},
    )


# Un Process válido tiene body REGION, hijos COMPONENT con rol y siempre un CENTER.
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


def _validate_time_status_state(manifest: ToolManifest, state: TimeStatusState) -> None:
    if state.tool_key != manifest.tool_key:
        raise ProcessCompositionError('Time status tool key does not match process manifest')


def _join_classes(*values: str | None) -> str:
    return ' '.join(value.strip() for value in values if value and value.strip())
