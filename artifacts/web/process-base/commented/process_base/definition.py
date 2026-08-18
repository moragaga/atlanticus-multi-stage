# Espejo comentado: parametrización concreta que un futuro repositorio Process reemplazará por su dominio.
from __future__ import annotations

from functools import partial

from dash import dcc, html

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
    ComponentBundle,
    ComponentProjectionDefinition,
    ComponentRendererDefinition,
    ComponentRendererRegistry,
    DashboardPollingSettings,
    DashboardToolConfiguration,
    TimeSeriesProjectionDefinition,
    TimeSeriesSettings,
)

_SCOPE = ToolScope.PLANT
_KPI = frozenset({ToolTarget.KPI})
_ALARM = frozenset({ToolTarget.ALARM})
_KPI_ALARM = frozenset({ToolTarget.KPI, ToolTarget.ALARM})


# Manifest de estrés: cuatro regiones Process y ocho cards para validar la geometría genérica.
def build_manifest():
    components = (
        _component('upstream', 'Aguas Arriba', ProcessBodySection.LEFT, _KPI),
        _component('main_process', 'Proceso Principal', ProcessBodySection.CENTER, _KPI_ALARM),
        _component('downstream', 'Aguas Abajo', ProcessBodySection.RIGHT, _KPI),
        _component('trends', 'Tendencias', ProcessBodySection.BOTTOM, _KPI),
    )
    cards = (
        _card('upstream', 'feed', 'Alimentación'),
        _card('upstream', 'quality', 'Calidad'),
        _card('main_process', 'primary', 'Principal', alarm=True),
        _card('main_process', 'secondary', 'Secundario', alarm=True),
        _card('main_process', 'recovery', 'Recuperación', alarm=True),
        _card('downstream', 'product', 'Producto'),
        _card('downstream', 'destination', 'Destino'),
        _card('trends', 'overview', 'Vista 24 h'),
    )
    return build_process_manifest(
        tool_key='process_base',
        display_name='Process Base',
        sources=(
            ToolSource(ToolSourceKey.PI, stale_after_seconds=300),
            ToolSource(ToolSourceKey.DISPATCH, stale_after_seconds=600),
        ),
        operational_scope=_SCOPE,
        body_sections=(*components, *cards),
    )


# Proyecciones de ejemplo: data y ventanas 1 h / 5 h / 24 h sin conocimiento del layout.
def build_dashboard_configuration() -> DashboardToolConfiguration:
    return DashboardToolConfiguration(
        components=(
            ComponentProjectionDefinition(component_key='upstream', data=True),
            ComponentProjectionDefinition(
                component_key='main_process',
                data=True,
                time_series=(
                    TimeSeriesProjectionDefinition(key='primary', hours=1),
                    TimeSeriesProjectionDefinition(key='recovery', hours=5),
                ),
            ),
            ComponentProjectionDefinition(component_key='downstream', data=True),
            ComponentProjectionDefinition(
                component_key='trends',
                data=True,
                time_series=(TimeSeriesProjectionDefinition(key='overview', hours=24),),
            ),
        ),
        time_series=TimeSeriesSettings(
            step_seconds=60,
            display_timezone='America/Santiago',
        ),
    )


# Los renderers son la única UI de negocio que el artifact aporta a la composition.
def build_renderer_registry() -> ComponentRendererRegistry:
    return ComponentRendererRegistry(
        definitions=tuple(
            ComponentRendererDefinition(
                component_key=component_key,
                renderer=partial(_render_component, component_key=component_key),
            )
            for component_key in ('upstream', 'main_process', 'downstream', 'trends')
        )
    )


def build_polling_settings() -> DashboardPollingSettings:
    return DashboardPollingSettings(interval_seconds=2)


def _component(
    key: str,
    display_name: str,
    role: ProcessBodySection,
    targets: frozenset[ToolTarget],
) -> ToolSection:
    return ToolSection(
        key=key,
        display_name=display_name,
        kind=ToolSectionKind.COMPONENT,
        scope=_SCOPE,
        parent_key='body',
        targets=targets,
        layout_role=role,
    )


def _card(
    component: str,
    subcomponent: str,
    display_name: str,
    *,
    alarm: bool = False,
) -> ToolSection:
    return ToolSection(
        component=component,
        subcomponent=subcomponent,
        display_name=display_name,
        kind=ToolSectionKind.SUBCOMPONENT,
        scope=_SCOPE,
        targets=_ALARM if alarm else (),
    )


def _render_component(bundle: ComponentBundle, *, component_key: str):
    values = bundle.data or {}
    return {
        subcomponent: _render_card(bundle, subcomponent=subcomponent, value=value)
        for subcomponent, value in values.items()
        if subcomponent in _expected_subcomponents(component_key)
    }


# Plotly vive dentro del ContentSlot genérico; no recibe permiso para gobernar el viewport.
def _render_card(
    bundle: ComponentBundle,
    *,
    subcomponent: str,
    value: object,
):
    children = [
        html.Div(_display_value(value), className='process-base__value'),
    ]
    window = next(
        (item for item in bundle.time_series.values() if subcomponent in item.series),
        None,
    )
    if window is not None:
        children.append(
            dcc.Graph(
                figure={
                    'data': [
                        {
                            'type': 'scatter',
                            'mode': 'lines',
                            'x': [item.isoformat() for item in window.axis.utc],
                            'y': list(window.series[subcomponent]),
                            'customdata': list(window.axis.labels),
                            'hovertemplate': '%{customdata}<br>%{y}<extra></extra>',
                        }
                    ],
                    'layout': {
                        'autosize': True,
                        'margin': {'l': 26, 'r': 8, 't': 5, 'b': 20},
                        'showlegend': False,
                        'xaxis': {'showticklabels': False, 'fixedrange': True},
                        'yaxis': {'fixedrange': True},
                    },
                },
                config={'displayModeBar': False, 'responsive': True},
                className='process-base__graph',
                style={'height': '100%', 'minHeight': 0},
            )
        )
    return html.Div(children, className='process-base__card-content')


def _expected_subcomponents(component_key: str) -> frozenset[str]:
    return {
        'upstream': frozenset({'feed', 'quality'}),
        'main_process': frozenset({'primary', 'secondary', 'recovery'}),
        'downstream': frozenset({'product', 'destination'}),
        'trends': frozenset({'overview'}),
    }[component_key]


def _display_value(value: object) -> str:
    if value is None:
        return '—'
    if isinstance(value, float):
        return f'{value:.1f}'
    return str(value)
