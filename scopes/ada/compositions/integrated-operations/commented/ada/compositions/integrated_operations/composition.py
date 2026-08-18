# Espejo comentado: ensambla la herramienta IO completa sin reimplementar sus capabilities.
from __future__ import annotations

from dataclasses import dataclass

from dash import html
from dash.development.base_component import Component

from ada.contracts.tool_manifest import ToolManifest, ToolScope, ToolSectionKind
from ada.features.alarms import (
    AlarmPresentationInteraction,
    alarm_geometry_scope_attributes,
    alarm_presentation_scope_attributes,
    build_alarm_dashboard_route_layer,
    build_integrated_operations_alarm_baseline,
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
from ada.ui.components.state_wrapper import ComponentCover, build_state_overlay, build_state_wrapper
from ada.ui.framework.core import build_ready_scope
from ada.ui.layouts.integrated_operations import build_integrated_operations_layout
from ada.ui.shell.header import HeaderState, build_ada_header
from ada.ui.shell.time_status import TimeStatusState, build_ada_time_status

from .errors import IntegratedOperationsCompositionError

_MINE_COMPONENT_KEYS = (
    'general_mina',
    'carguio',
    'transporte',
    'chancado_stmg',
)
_PLANT_COMPONENT_KEYS = (
    'stockpile_chacay',
    'molienda',
    'flotacion',
    'transporte_fluidos',
    'puerto',
)
_COMPONENT_KEYS = (*_MINE_COMPONENT_KEYS, *_PLANT_COMPONENT_KEYS)
_SHARED_COMPONENT = 'carguio'
_SHARED_SUBCOMPONENT = 'gestion_carguio_turno'


@dataclass(frozen=True, slots=True)
class IntegratedOperationsToolComposition:
    dashboard: DashboardDefinition
    mount: DashboardMount

    @property
    def manifest(self) -> ToolManifest:
        return self.dashboard.manifest

    def build_body(self, *, layout_id: str | None = None) -> html.Div:
        content = {
            component_key: _build_component_cards(
                self.manifest,
                component_key=component_key,
                mount=self.mount,
            )
            for component_key in _COMPONENT_KEYS
        }
        return build_integrated_operations_layout(
            self.manifest,
            component_content=content,
            shared_card_content=_build_shared_card(self.manifest),
            layout_id=layout_id,
            class_name='ada-integrated-operations-tool__layout',
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
        children: list[Component] = [
            build_ada_header(
                header_state,
                alarm_management_slot=(
                    alarm_management_slot
                    if alarm_management_slot is not None
                    else build_alarm_management_summary(None, cover=ComponentCover.construction())
                ),
                alarm_status_slot=(
                    alarm_status_slot
                    if alarm_status_slot is not None
                    else build_alarm_status(None, cover=ComponentCover.construction())
                ),
                desktop_navigation_trigger=desktop_navigation_trigger,
                mobile_navigation_trigger=mobile_navigation_trigger,
            ),
            html.Div(
                _build_time_status(self.manifest, time_status_state),
                className='ada-integrated-operations-tool__time-status',
            ),
            _build_alarm_surface(self.manifest, alarm_content),
            html.Main(
                self.build_body(layout_id=layout_id),
                className='ada-integrated-operations-tool__body',
            ),
            self.mount.runtime_host(),
        ]
        return build_ready_scope(
            content=html.Div(
                children,
                className=_join_classes('ada-integrated-operations-tool', class_name),
                **{
                    'data-ada-integrated-operations-tool': self.manifest.tool_key,
                    'data-ada-io-presentation': 'overview',
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


def create_integrated_operations_tool_composition(
    manifest: ToolManifest,
    *,
    dashboard_configuration: DashboardToolConfiguration | None = None,
    renderers: ComponentRendererRegistry | None = None,
    polling: DashboardPollingSettings | None = None,
    dashboard_key: str | None = None,
) -> IntegratedOperationsToolComposition:
    _validate_integrated_operations_manifest(manifest)
    dashboard = DashboardDefinition.build(
        manifest=manifest,
        configuration=dashboard_configuration or DashboardToolConfiguration(),
        renderers=renderers or ComponentRendererRegistry(),
        polling=polling,
    )
    return IntegratedOperationsToolComposition(
        dashboard=dashboard,
        mount=build_dashboard_mount(dashboard, dashboard_key=dashboard_key),
    )


def _build_component_cards(
    manifest: ToolManifest,
    *,
    component_key: str,
    mount: DashboardMount,
) -> html.Div:
    cards = []
    for section in manifest.children(component_key):
        if section.subcomponent is None or section.linked_component_keys:
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
                class_name='ada-integrated-operations-tool__card',
            )
        )
    return html.Div(cards, className='ada-integrated-operations-tool__component-cards')


def _build_shared_card(manifest: ToolManifest) -> Component:
    section = manifest.subcomponent(
        component=_SHARED_COMPONENT,
        subcomponent=_SHARED_SUBCOMPONENT,
    )
    return build_component_card(
        manifest,
        component=_SHARED_COMPONENT,
        subcomponent=_SHARED_SUBCOMPONENT,
        label=section.display_name,
        overlay=build_state_overlay(ComponentCover.construction()),
        class_name=(
            'ada-integrated-operations-tool__card '
            'ada-integrated-operations-tool__shared-card'
        ),
    )


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


def _build_alarm_surface(manifest: ToolManifest, content: Component | None) -> html.Section:
    children: list[Component] = []
    if content is not None:
        children.append(
            html.Div(
                content,
                className='ada-integrated-operations-tool__alarm-content',
            )
        )
    component_scopes = {
        component_key: manifest.section(component_key).scope.value
        for component_key in _COMPONENT_KEYS
    }
    children.extend(
        (
            build_alarm_dashboard_route_layer(),
            build_integrated_operations_alarm_baseline(
                _COMPONENT_KEYS,
                component_scopes=component_scopes,
            ),
        )
    )
    return html.Section(
        children,
        className='ada-integrated-operations-tool__alarm-surface',
        **{'data-ada-integrated-operations-alarm-surface': 'true'},
    )


def _validate_integrated_operations_manifest(manifest: ToolManifest) -> None:
    if not isinstance(manifest, ToolManifest):
        raise IntegratedOperationsCompositionError(
            f'Invalid integrated operations tool manifest: {manifest!r}'
        )
    if manifest.tool_key != 'integrated_operations':
        raise IntegratedOperationsCompositionError(
            'Integrated operations composition requires tool manifest "integrated_operations"'
        )
    body = manifest.section('body')
    if body.kind is not ToolSectionKind.REGION:
        raise IntegratedOperationsCompositionError('Integrated operations body must be a region')
    expected = {
        ToolScope.MINE.value: set(_MINE_COMPONENT_KEYS),
        ToolScope.PLANT.value: set(_PLANT_COMPONENT_KEYS),
    }
    for scope_key, component_keys in expected.items():
        region = manifest.section(scope_key)
        if region.kind is not ToolSectionKind.REGION or region.parent_key != 'body':
            raise IntegratedOperationsCompositionError(
                f'Integrated operations section {scope_key!r} must be a body region'
            )
        if {section.key for section in manifest.children(scope_key)} != component_keys:
            raise IntegratedOperationsCompositionError(
                f'Integrated operations region {scope_key!r} does not match composition'
            )


def _validate_header_state(manifest: ToolManifest, state: HeaderState) -> None:
    if state.tool_key != manifest.tool_key:
        raise IntegratedOperationsCompositionError(
            'Header state tool key does not match integrated operations manifest'
        )


def _validate_time_status_state(manifest: ToolManifest, state: TimeStatusState) -> None:
    if state.tool_key != manifest.tool_key:
        raise IntegratedOperationsCompositionError(
            'Time status tool key does not match integrated operations manifest'
        )


def _join_classes(*values: str | None) -> str:
    return ' '.join(value.strip() for value in values if value and value.strip())
