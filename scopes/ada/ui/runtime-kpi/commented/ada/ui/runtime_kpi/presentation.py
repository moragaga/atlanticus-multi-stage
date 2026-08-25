# Espejo comentado: mantiene exactamente el comportamiento del archivo productivo.
# Construye wrappers runtime y representaciones visuales genéricas de estados KPI.
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from dash import html
from dash.development.base_component import Component

from ada.runtime.component_stores import RuntimeComponentStoreRegistry
from ada.ui.framework.core import DisplayStatus, resolve_status_visual

from .models import RuntimeKpiValue, RuntimeKpiValueKind

RuntimeKpiRenderer = Callable[[object], Any]


def build_runtime_component_wrapper(
    registry: RuntimeComponentStoreRegistry,
    *,
    component_key: str,
    content: Any = None,
    class_name: str | None = None,
) -> html.Section:
    spec = registry.component(component_key)
    return html.Section(
        content,
        id=spec.wrapper_id,
        className=_join_classes('ada-runtime-component', class_name),
        **{
            'data-ada-runtime-component': spec.component_key,
            'data-ada-runtime-wrapper': 'true',
        },
    )


def render_runtime_kpi_value(
    value: RuntimeKpiValue,
    *,
    value_renderer: RuntimeKpiRenderer | None = None,
    json_renderer: RuntimeKpiRenderer | None = None,
) -> Any:
    if value.status is not DisplayStatus.OK:
        return _build_status_visual(value.status)
    renderer = json_renderer if value.value_kind is RuntimeKpiValueKind.JSON else value_renderer
    if renderer is not None:
        try:
            return renderer(value.value)
        except Exception:
            return _build_status_visual(DisplayStatus.INVALID)
    if value.value_kind is RuntimeKpiValueKind.JSON:
        return _build_status_visual(DisplayStatus.INVALID)
    return value.value


def _build_status_visual(status: DisplayStatus) -> Component | str:
    visual = resolve_status_visual(status)
    if visual is None:
        visual = resolve_status_visual(DisplayStatus.ERROR)
    if visual is None:
        return '-'
    return html.Img(
        src=visual.asset_url,
        alt=visual.alt,
        title=visual.title,
        className='ada-status-icon ada-runtime-kpi__status-icon',
    )


def _join_classes(*values: str | None) -> str:
    return ' '.join(value.strip() for value in values if value and value.strip())
