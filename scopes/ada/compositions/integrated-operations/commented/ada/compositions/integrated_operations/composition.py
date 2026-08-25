from __future__ import annotations

from dataclasses import dataclass

from dash import html
from dash.development.base_component import Component

from ada.configuration.tools import ToolConfigurationProjection
from ada.contracts.tool_manifest import ToolManifest, ToolScope, ToolSectionKind
from ada.features.alarms import (
    AlarmPresentationInteraction,
    alarm_geometry_scope_attributes,
    alarm_presentation_scope_attributes,
    build_alarm_dashboard_route_layer,
    build_integrated_operations_alarm_baseline,
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
from ada.ui.components.state_wrapper import ComponentCover, build_state_overlay
from ada.ui.layouts.integrated_operations import build_integrated_operations_layout
from ada.ui.shell.header import HeaderState
from ada.ui.shell.operational import build_ada_operational_shell
from ada.ui.shell.time_status import TimeStatusState

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


# IO conserva su presentación específica y consume la misma autoridad runtime genérica que Process.
@dataclass(frozen=True, slots=True)
class IntegratedOperationsToolComposition:
    dashboard: DashboardDefinition
    mount: DashboardMount
    projection: ToolConfigurationProjection | None = None
    runtime_store_mount: RuntimeComponentStoreMount | None = None

    @property
    def manifest(self) -> ToolManifest:
        return self.dashboard.manifest

    def build_body(self, *, layout_id: str | None = None) -> html.Div:
        # Los componentes 4+5 mantienen su posición y sólo reciben identidad runtime adicional.
        content = {
            component_key: _build_component_cards(
                self.manifest,
                component_key=component_key,
                mount=self.mount,
                projection=self.projection,
            )
            for component_key in _COMPONENT_KEYS
        }
        return build_integrated_operations_layout(
            self.manifest,
            component_content=content,
            shared_card_content=_build_shared_card(
                self.manifest,
                projection=self.projection,
            ),
            component_wrapper_ids=_component_wrapper_ids(self.projection),
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
        _validate_time_status_state(self.manifest, time_status_state)
        # Header, Time Status y Body comparten los mismos wrapper ids derivados de la proyección.
        return build_ada_operational_shell(
            self.manifest,
            header_state=header_state,
            body_content=[
                self.build_body(layout_id=layout_id),
                _build_zoom_controls(),
            ],
            alarm_children=_build_alarm_children(self.manifest, alarm_content),
            alarm_management_slot=alarm_management_slot,
            alarm_status_slot=alarm_status_slot,
            time_status_state=time_status_state,
            desktop_navigation_trigger=desktop_navigation_trigger,
            mobile_navigation_trigger=mobile_navigation_trigger,
            runtime_hosts=_runtime_hosts(self.mount, self.runtime_store_mount),
            runtime_component_wrapper_ids=_component_wrapper_ids(self.projection),
            shell_class_name=_join_classes('ada-integrated-operations-tool', class_name),
            time_status_class_name='ada-integrated-operations-tool__time-status',
            alarm_surface_class_name='ada-integrated-operations-tool__alarm-surface',
            body_class_name='ada-integrated-operations-tool__body',
            shell_style={
                '--ada-io-overview-indicator-count': str(
                    max(1, len(header_state.global_indicators))
                ),
            },
            shell_attributes={
                'data-ada-integrated-operations-tool': self.manifest.tool_key,
                'data-ada-io-presentation': 'overview',
                **alarm_geometry_scope_attributes(),
                **alarm_presentation_scope_attributes(
                    trace_dwell_ms=alarm_trace_dwell_ms,
                    interaction=alarm_interaction,
                ),
            },
            alarm_surface_attributes={
                'data-ada-integrated-operations-alarm-surface': 'true',
            },
        )


def create_integrated_operations_tool_composition(
    manifest: ToolManifest,
    *,
    projection: ToolConfigurationProjection | None = None,
    dashboard_configuration: DashboardToolConfiguration | None = None,
    renderers: ComponentRendererRegistry | None = None,
    polling: DashboardPollingSettings | None = None,
    dashboard_key: str | None = None,
) -> IntegratedOperationsToolComposition:
    _validate_integrated_operations_manifest(manifest)
    # La proyección sigue opcional hasta que el artifact la entregue; si existe debe coincidir.
    _validate_projection(manifest, projection)
    dashboard = DashboardDefinition.build(
        manifest=manifest,
        configuration=dashboard_configuration or DashboardToolConfiguration(),
        renderers=renderers or ComponentRendererRegistry(),
        polling=polling,
    )
    # Los stores R3 se agregan sin introducir un segundo runtime ni alterar la superficie visible.
    runtime_store_mount = _build_runtime_store_mount(projection)
    return IntegratedOperationsToolComposition(
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
        if section.subcomponent is None or section.linked_component_keys:
            continue
        slot = mount.slot(component_key, section.subcomponent)
        # Cada card normal recibe el wrapper canónico de su subcomponente.
        cards.append(
            build_component_card(
                manifest,
                component=component_key,
                subcomponent=section.subcomponent,
                content=slot.content,
                label=section.display_name,
                overlay=slot.overlay,
                class_name='ada-integrated-operations-tool__card',
                wrapper_id=_subcomponent_wrapper_id(
                    projection,
                    component_key=component_key,
                    subcomponent_key=section.subcomponent,
                ),
            )
        )
    return html.Div(cards, className='ada-integrated-operations-tool__component-cards')


def _build_shared_card(
    manifest: ToolManifest,
    *,
    projection: ToolConfigurationProjection | None,
) -> Component:
    section = manifest.subcomponent(
        component=_SHARED_COMPONENT,
        subcomponent=_SHARED_SUBCOMPONENT,
    )
    # La card compartida se crea una sola vez; linked_component_keys no generan una copia adicional.
    return build_component_card(
        manifest,
        component=_SHARED_COMPONENT,
        subcomponent=_SHARED_SUBCOMPONENT,
        label=section.display_name,
        overlay=build_state_overlay(ComponentCover.construction()),
        class_name=(
            'ada-integrated-operations-tool__card ada-integrated-operations-tool__shared-card'
        ),
        wrapper_id=_subcomponent_wrapper_id(
            projection,
            component_key=_SHARED_COMPONENT,
            subcomponent_key=_SHARED_SUBCOMPONENT,
        ),
    )


def _build_alarm_children(
    manifest: ToolManifest,
    content: Component | None,
) -> tuple[Component, ...]:
    component_scopes = {
        component_key: manifest.section(component_key).scope.value
        for component_key in _COMPONENT_KEYS
    }
    return (
        html.Div(
            [] if content is None else [content],
            className='ada-integrated-operations-tool__alarm-content',
        ),
        build_alarm_dashboard_route_layer(),
        build_integrated_operations_alarm_baseline(
            _COMPONENT_KEYS,
            component_scopes=component_scopes,
        ),
        _build_overview_controls(),
    )


def _build_runtime_store_mount(
    projection: ToolConfigurationProjection | None,
) -> RuntimeComponentStoreMount | None:
    if projection is None:
        return None
    # El registry existente conserva ids de stores y wrappers definidos por Tool Projection.
    return build_runtime_component_store_mount(build_runtime_component_store_registry(projection))


def _runtime_hosts(
    dashboard_mount: DashboardMount,
    runtime_store_mount: RuntimeComponentStoreMount | None,
) -> tuple[Component, ...]:
    # Dashboard y stores viven como hosts ocultos independientes de la geometría IO.
    hosts: list[Component] = [dashboard_mount.runtime_host()]
    if runtime_store_mount is not None:
        hosts.append(runtime_store_mount.runtime_host())
    return tuple(hosts)


def _component_wrapper_ids(
    projection: ToolConfigurationProjection | None,
) -> dict[str, str]:
    if projection is None:
        return {}
    # Las claves funcionales son la frontera estable entre configuración y presentación.
    return {binding.component_key: binding.wrapper_id for binding in projection.runtime.components}


def _subcomponent_wrapper_id(
    projection: ToolConfigurationProjection | None,
    *,
    component_key: str,
    subcomponent_key: str,
) -> str | None:
    if projection is None:
        return None
    # El resolver del contrato devuelve el mismo binding para el subcomponente compartido.
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
        raise IntegratedOperationsCompositionError(
            f'Invalid integrated operations tool projection: {projection!r}'
        )
    # Se distingue mismatch de identidad de mismatch estructural para diagnosticar configuración.
    if projection.manifest.tool_key != manifest.tool_key:
        raise IntegratedOperationsCompositionError(
            'Tool projection tool key does not match integrated operations manifest'
        )
    if projection.manifest != manifest:
        raise IntegratedOperationsCompositionError(
            'Tool projection manifest does not match integrated operations manifest'
        )


def _build_overview_controls() -> html.Div:
    return html.Div(
        [
            _build_presentation_button(
                'MINA',
                target='mine',
                class_name='ada-integrated-operations-tool__overview-control--mine',
                aria_label='Ampliar Mina',
            ),
            _build_presentation_button(
                'PLANTA',
                target='plant',
                class_name='ada-integrated-operations-tool__overview-control--plant',
                aria_label='Ampliar Planta',
            ),
        ],
        className='ada-integrated-operations-tool__overview-controls',
    )


def _build_zoom_controls() -> html.Div:
    return html.Div(
        [
            _build_presentation_button(
                '×',
                target='overview',
                class_name='ada-integrated-operations-tool__zoom-close',
                aria_label='Volver a vista general',
            ),
            _build_presentation_button(
                '‹ MINA',
                target='mine',
                class_name=(
                    'ada-integrated-operations-tool__zoom-side '
                    'ada-integrated-operations-tool__zoom-side--mine'
                ),
                aria_label='Cambiar a Mina',
            ),
            _build_presentation_button(
                'PLANTA ›',
                target='plant',
                class_name=(
                    'ada-integrated-operations-tool__zoom-side '
                    'ada-integrated-operations-tool__zoom-side--plant'
                ),
                aria_label='Cambiar a Planta',
            ),
        ],
        className='ada-integrated-operations-tool__zoom-controls',
    )


def _build_presentation_button(
    label: str,
    *,
    target: str,
    class_name: str,
    aria_label: str,
) -> html.Button:
    return html.Button(
        label,
        type='button',
        className=(f'ada-integrated-operations-tool__presentation-button {class_name}'),
        **{
            'aria-label': aria_label,
            'data-ada-io-presentation-target': target,
        },
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


def _validate_time_status_state(
    manifest: ToolManifest,
    state: TimeStatusState | None,
) -> None:
    if state is not None and state.tool_key != manifest.tool_key:
        raise IntegratedOperationsCompositionError(
            'Time status tool key does not match integrated operations manifest'
        )


def _join_classes(*values: str | None) -> str:
    return ' '.join(value.strip() for value in values if value and value.strip())
