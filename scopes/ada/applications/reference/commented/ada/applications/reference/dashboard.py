from __future__ import annotations
# Espejo comentado: conserva la misma lógica productiva y documenta su responsabilidad.

from collections.abc import Mapping
from dataclasses import dataclass
from functools import partial
from types import MappingProxyType

from dash import Dash, dcc, html

from ada.applications.reference.process import reference_process_variants
from ada.applications.reference.snapshot_repository import ReferenceSnapshotRepository
from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ToolManifest,
    ToolSectionKind,
)
from ada.features.dashboard import (
    ADA_DASHBOARD_ASSET_LAYER,
    ComponentBundle,
    ComponentProjectionDefinition,
    ComponentRendererDefinition,
    ComponentRendererRegistry,
    DashboardDefinition,
    DashboardMount,
    DashboardPollingSettings,
    DashboardToolConfiguration,
    TimeSeriesProjectionDefinition,
    TimeSeriesSettings,
    build_dashboard_mount,
    register_dashboard_callbacks,
    register_dashboard_polling_callbacks,
)
from ada.runtime.web import SharedSnapshotReader
from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry

_REFERENCE_POLLING_SECONDS = 2.0
_REFERENCE_STEP_SECONDS = 60
_REFERENCE_TIMEZONE = 'America/Santiago'

_IO_TIME_SERIES = {
    'stockpile_chacay': (('tendencia_alimentado', 5),),
    'molienda': (('molienda', 1),),
    'flotacion': (('colectiva', 1), ('selectiva', 5)),
}

_PROCESS_TIME_SERIES = {
    'process_center_right_reference': {
        'planta_molibdeno': (('rougher', 1), ('cleaner', 5)),
        'aguas_abajo': (('stc', 1),),
    },
    'process_full_reference': {
        'aguas_arriba': (('tendencias_courier', 5),),
        'planta_molibdeno': (('principal', 1),),
    },
    'process_full_bottom_reference': {
        'planta_molibdeno': (('principal', 1),),
        'graficas_tendencia': (('graficas', 24),),
    },
}


@dataclass(frozen=True, slots=True)
class ReferenceDashboard:
    definition: DashboardDefinition

    def mount(self) -> DashboardMount:
        return build_dashboard_mount(self.definition)


@dataclass(frozen=True, slots=True)
class ReferenceDashboardCatalog:
    dashboards: Mapping[str, ReferenceDashboard]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'dashboards', MappingProxyType(dict(self.dashboards)))

    def dashboard(self, tool_key: str) -> ReferenceDashboard:
        return self.dashboards[tool_key]

    @property
    def definitions(self) -> Mapping[str, DashboardDefinition]:
        return {
            tool_key: dashboard.definition
            for tool_key, dashboard in self.dashboards.items()
        }


def build_reference_dashboard_catalog() -> ReferenceDashboardCatalog:
    manifests = [INTEGRATED_OPERATIONS_MANIFEST]
    manifests.extend(variant.manifest for variant in reference_process_variants())
    dashboards: dict[str, ReferenceDashboard] = {}
    for manifest in manifests:
        definition = _build_dashboard_definition(manifest)
        dashboards[manifest.tool_key] = ReferenceDashboard(definition=definition)
    return ReferenceDashboardCatalog(dashboards=dashboards)


def create_reference_dashboard_module(
    catalog: ReferenceDashboardCatalog,
) -> WebModule:
    repository = ReferenceSnapshotRepository(catalog.definitions)
    reader = SharedSnapshotReader(repository, ttl_seconds=1.0)
    return WebModule(
        name='ada-dashboard-reference',
        # Reference registra callbacks propios, pero reutiliza la misma frontera visual del feature.
        asset_layers=(ADA_DASHBOARD_ASSET_LAYER,),
        register_callbacks=partial(
            _register_callbacks,
            catalog=catalog,
            reader=reader,
        ),
    )


def _register_callbacks(
    app: Dash,
    _services: ServiceRegistry,
    *,
    catalog: ReferenceDashboardCatalog,
    reader: SharedSnapshotReader,
) -> None:
    for dashboard in catalog.dashboards.values():
        register_dashboard_callbacks(app, dashboard.definition)
        register_dashboard_polling_callbacks(app, dashboard.definition, reader)


def _build_dashboard_definition(manifest: ToolManifest) -> DashboardDefinition:
    time_series_by_component = _time_series_for_tool(manifest.tool_key)
    components = tuple(_body_components(manifest))
    configuration = DashboardToolConfiguration(
        components=tuple(
            ComponentProjectionDefinition(
                component_key=component.key,
                data=True,
                time_series=tuple(
                    TimeSeriesProjectionDefinition(key=key, hours=hours)
                    for key, hours in time_series_by_component.get(component.key, ())
                ),
            )
            for component in components
        ),
        time_series=(
            TimeSeriesSettings(
                step_seconds=_REFERENCE_STEP_SECONDS,
                display_timezone=_REFERENCE_TIMEZONE,
            )
            if time_series_by_component
            else None
        ),
    )
    renderers = ComponentRendererRegistry(
        definitions=tuple(
            ComponentRendererDefinition(
                component_key=component.key,
                renderer=partial(
                    _render_component,
                    manifest=manifest,
                    component_key=component.key,
                ),
            )
            for component in components
        )
    )
    return DashboardDefinition.build(
        manifest=manifest,
        configuration=configuration,
        renderers=renderers,
        polling=DashboardPollingSettings(interval_seconds=_REFERENCE_POLLING_SECONDS),
    )


def _body_components(manifest: ToolManifest):
    pending = list(manifest.children('body'))
    while pending:
        section = pending.pop(0)
        if section.kind is ToolSectionKind.COMPONENT:
            yield section
            continue
        if section.kind is ToolSectionKind.REGION:
            pending[0:0] = manifest.children(section.key)


def _time_series_for_tool(tool_key: str) -> Mapping[str, tuple[tuple[str, int], ...]]:
    if tool_key == INTEGRATED_OPERATIONS_MANIFEST.tool_key:
        return _IO_TIME_SERIES
    return _PROCESS_TIME_SERIES.get(tool_key, {})


def _render_component(
    bundle: ComponentBundle,
    *,
    manifest: ToolManifest,
    component_key: str,
):
    payload = bundle.data or {}
    return {
        section.subcomponent: _card_content(
            bundle,
            subcomponent=section.subcomponent,
            value=payload.get(section.subcomponent),
        )
        for section in manifest.children(component_key)
        if section.subcomponent is not None and not section.linked_component_keys
    }


def _card_content(
    bundle: ComponentBundle,
    *,
    subcomponent: str,
    value: object,
):
    series_window = next(
        (
            window
            for window in bundle.time_series.values()
            if subcomponent in window.series
        ),
        None,
    )
    children = [
        html.Div(
            _display_value(value),
            className='reference-ada__dashboard-value',
        )
    ]
    if series_window is not None:
        children.append(
            dcc.Graph(
                figure=_series_figure(series_window, subcomponent),
                config={'displayModeBar': False, 'responsive': True},
                className='reference-ada__dashboard-series',
            )
        )
    return html.Div(children, className='reference-ada__dashboard-card-content')


def _series_figure(window, series_key: str) -> dict[str, object]:
    values = window.series[series_key]
    return {
        'data': [
            {
                'type': 'scatter',
                'mode': 'lines',
                'x': [value.isoformat() for value in window.axis.utc],
                'y': list(values),
                'customdata': list(window.axis.labels),
                'hovertemplate': '%{customdata}<br>%{y}<extra></extra>',
            }
        ],
        'layout': {
            'height': 112,
            'margin': {'l': 24, 'r': 8, 't': 4, 'b': 18},
            'showlegend': False,
            'xaxis': {'showticklabels': False, 'fixedrange': True},
            'yaxis': {'fixedrange': True},
        },
    }


def _display_value(value: object) -> str:
    if value is None:
        return '—'
    if isinstance(value, float):
        return f'{value:.1f}'
    return str(value)
