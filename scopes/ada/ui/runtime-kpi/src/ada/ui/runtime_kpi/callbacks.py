from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from dash import Input, Output

from ada.runtime.component_stores import RuntimeComponentStoreRegistry
from ada.ui.framework.core import DisplayStatus

from .errors import RuntimeKpiUiError
from .models import RuntimeKpiValue, RuntimeTimeseriesSnapshot
from .normalization import decode_timeseries_store, normalize_latest_value
from .presentation import RuntimeKpiRenderer, render_runtime_kpi_value


@dataclass(frozen=True, slots=True)
class RuntimeLatestOutputBinding:
    output_id: str
    kpi_key: str
    output_property: str = 'children'
    value_renderer: RuntimeKpiRenderer | None = None
    json_renderer: RuntimeKpiRenderer | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, 'output_id', _require_text(self.output_id, 'Latest output id'))
        object.__setattr__(self, 'kpi_key', _require_text(self.kpi_key, 'Latest KPI key'))
        object.__setattr__(
            self,
            'output_property',
            _require_text(self.output_property, 'Latest output property'),
        )


RuntimeTimeseriesRenderer = Callable[[RuntimeTimeseriesSnapshot], Any]


def register_runtime_latest_callback(
    app: Any,
    *,
    registry: RuntimeComponentStoreRegistry,
    component_key: str,
    bindings: tuple[RuntimeLatestOutputBinding, ...],
) -> None:
    resolved_component = registry.component(component_key)
    resolved_bindings = tuple(bindings)
    if not resolved_bindings:
        raise RuntimeKpiUiError('Runtime Latest callback requires at least one output binding')
    outputs = tuple(
        Output(binding.output_id, binding.output_property) for binding in resolved_bindings
    )

    @app.callback(
        *outputs,
        Input(resolved_component.latest_store_id, 'data'),
        prevent_initial_call=False,
    )
    def render_latest(store_value: object):
        rendered = tuple(
            render_runtime_kpi_value(
                normalize_latest_value(store_value, kpi_key=binding.kpi_key),
                value_renderer=binding.value_renderer,
                json_renderer=binding.json_renderer,
            )
            for binding in resolved_bindings
        )
        if len(rendered) == 1:
            return rendered[0]
        return rendered


def register_runtime_timeseries_callback(
    app: Any,
    *,
    registry: RuntimeComponentStoreRegistry,
    component_key: str,
    output_id: str,
    renderer: RuntimeTimeseriesRenderer,
    output_property: str = 'children',
) -> None:
    resolved_component = registry.component(component_key)
    resolved_output_id = _require_text(output_id, 'Timeseries output id')
    resolved_output_property = _require_text(output_property, 'Timeseries output property')
    if not callable(renderer):
        raise RuntimeKpiUiError('Timeseries renderer must be callable')

    @app.callback(
        Output(resolved_output_id, resolved_output_property),
        Input(resolved_component.timeseries_store_id, 'data'),
        prevent_initial_call=False,
    )
    def render_timeseries(store_value: object):
        try:
            snapshot = decode_timeseries_store(store_value)
        except RuntimeKpiUiError:
            return render_runtime_kpi_value(RuntimeKpiValue(DisplayStatus.INVALID))
        if snapshot is None:
            return render_runtime_kpi_value(RuntimeKpiValue(DisplayStatus.NOT_MAPPED))
        try:
            return renderer(snapshot)
        except Exception:
            return render_runtime_kpi_value(RuntimeKpiValue(DisplayStatus.INVALID))


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeKpiUiError(f'{label} cannot be empty')
    return value.strip()
