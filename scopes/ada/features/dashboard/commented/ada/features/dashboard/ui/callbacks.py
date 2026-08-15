from __future__ import annotations
# Espejo comentado: conserva la misma lógica productiva y documenta su responsabilidad.

from functools import partial

from dash import Dash, Input, Output, no_update

from ada.ui.components.state_wrapper import build_state_overlay

from ada.features.dashboard.core.definition import (
    DashboardComponentDefinition,
    DashboardDefinition,
)
from .ids import DashboardComponentIds, DashboardSubcomponentIds
from .wiring import (
    ComponentRenderErrorHandler,
    encode_render_status,
    render_component_from_stores,
    resolve_subcomponent_cover,
)


def register_dashboard_callbacks(
    app: Dash,
    definition: DashboardDefinition,
    *,
    dashboard_key: str | None = None,
    on_error: ComponentRenderErrorHandler | None = None,
) -> None:
    resolved_dashboard_key = dashboard_key or definition.manifest.tool_key
    for component in definition.components:
        if not component.callback_required:
            continue
        component_ids = DashboardComponentIds(
            resolved_dashboard_key,
            component.section.key,
        )
        subcomponent_ids = tuple(
            DashboardSubcomponentIds(
                resolved_dashboard_key,
                component.section.key,
                section.key,
            )
            for section in component.subcomponents
        )
        _register_render_callback(
            app,
            definition=definition,
            component=component,
            component_ids=component_ids,
            subcomponent_ids=subcomponent_ids,
            on_error=on_error,
        )
        _register_state_callback(
            app,
            component=component,
            component_ids=component_ids,
            subcomponent_ids=subcomponent_ids,
        )


def _register_render_callback(
    app: Dash,
    *,
    definition: DashboardDefinition,
    component: DashboardComponentDefinition,
    component_ids: DashboardComponentIds,
    subcomponent_ids: tuple[DashboardSubcomponentIds, ...],
    on_error: ComponentRenderErrorHandler | None,
) -> None:
    projection = component.projection
    if projection is None:
        return
    inputs: list[Input] = []
    if projection.data:
        inputs.append(Input(component_ids.data_store, 'data'))
    if projection.time_series:
        inputs.append(Input(component_ids.time_series_store, 'data'))

    callback = partial(
        _render_callback,
        component=component,
        definition=definition,
        on_error=on_error,
    )
    outputs = [Output(ids.content, 'children') for ids in subcomponent_ids]
    outputs.append(Output(component_ids.render_status_store, 'data'))
    app.callback(
        *outputs,
        *inputs,
        prevent_initial_call=False,
    )(callback)


def _register_state_callback(
    app: Dash,
    *,
    component: DashboardComponentDefinition,
    component_ids: DashboardComponentIds,
    subcomponent_ids: tuple[DashboardSubcomponentIds, ...],
) -> None:
    if not subcomponent_ids:
        return
    outputs = [Output(ids.overlay, 'children') for ids in subcomponent_ids]
    app.callback(
        *outputs,
        Input(component_ids.state_store, 'data'),
        Input(component_ids.render_status_store, 'data'),
        prevent_initial_call=False,
    )(
        partial(
            _state_callback,
            component=component,
        )
    )


def _render_callback(
    *values: object,
    component: DashboardComponentDefinition,
    definition: DashboardDefinition,
    on_error: ComponentRenderErrorHandler | None,
):
    projection = component.projection
    if projection is None:
        return (*([no_update] * len(component.subcomponents)), no_update)
    index = 0
    data_value = None
    time_series_value = None
    if projection.data:
        data_value = values[index]
        index += 1
    if projection.time_series:
        time_series_value = values[index]

    result = render_component_from_stores(
        component=component,
        configuration=definition.configuration,
        data_value=data_value,
        time_series_value=time_series_value,
        on_error=on_error,
    )
    if result.preserve_content or result.content is None:
        content = [no_update] * len(component.subcomponents)
    else:
        content = [
            result.content[section.subcomponent]
            for section in component.subcomponents
            if section.subcomponent is not None
        ]
    return (*content, encode_render_status(result.status))


def _state_callback(
    state_value: object,
    render_status_value: object,
    *,
    component: DashboardComponentDefinition,
):
    covers = [
        resolve_subcomponent_cover(
            component_key=component.section.key,
            subcomponent_key=section.subcomponent,
            state_value=state_value,
            render_status_value=render_status_value,
        )
        for section in component.subcomponents
        if section.subcomponent is not None
    ]
    overlays = [build_state_overlay(cover) for cover in covers]
    if len(overlays) == 1:
        return overlays[0]
    return tuple(overlays)
