from __future__ import annotations

from functools import partial

from dash import Dash, Input, Output, no_update

from ada.ui.components.state_wrapper import build_state_overlay

from .definition import DashboardComponentDefinition, DashboardDefinition
from .ids import DashboardComponentIds
from .wiring import (
    ComponentRenderErrorHandler,
    encode_render_status,
    render_component_from_stores,
    resolve_component_cover,
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
        ids = DashboardComponentIds(resolved_dashboard_key, component.section.key)
        _register_render_callback(
            app,
            definition=definition,
            component=component,
            ids=ids,
            on_error=on_error,
        )
        _register_state_callback(app, component=component, ids=ids)


def _register_render_callback(
    app: Dash,
    *,
    definition: DashboardDefinition,
    component: DashboardComponentDefinition,
    ids: DashboardComponentIds,
    on_error: ComponentRenderErrorHandler | None,
) -> None:
    projection = component.projection
    if projection is None:
        return
    inputs: list[Input] = []
    if projection.data:
        inputs.append(Input(ids.data_store, 'data'))
    if projection.time_series:
        inputs.append(Input(ids.time_series_store, 'data'))

    callback = partial(
        _render_callback,
        component=component,
        definition=definition,
        on_error=on_error,
    )
    app.callback(
        Output(ids.content, 'children'),
        Output(ids.render_status_store, 'data'),
        *inputs,
        prevent_initial_call=False,
    )(callback)


def _register_state_callback(
    app: Dash,
    *,
    component: DashboardComponentDefinition,
    ids: DashboardComponentIds,
) -> None:
    app.callback(
        Output(ids.overlay, 'children'),
        Input(ids.state_store, 'data'),
        Input(ids.render_status_store, 'data'),
        prevent_initial_call=False,
    )(
        partial(
            _state_callback,
            component_key=component.section.key,
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
        return no_update, no_update
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
    content = no_update if result.preserve_content else result.content
    return content, encode_render_status(result.status)


def _state_callback(
    state_value: object,
    render_status_value: object,
    *,
    component_key: str,
):
    cover = resolve_component_cover(
        component_key=component_key,
        state_value=state_value,
        render_status_value=render_status_value,
    )
    return build_state_overlay(cover)
