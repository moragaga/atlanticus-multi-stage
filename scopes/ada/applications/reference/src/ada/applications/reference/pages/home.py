from dash import html, register_page

from ada.applications.reference.alarm_dashboard import build_reference_alarm_interaction
from ada.applications.reference.dashboard import build_reference_dashboard_catalog
from ada.applications.reference.integrated_operations import (
    build_reference_integrated_operations_layout,
)
from ada.applications.reference.process import build_reference_process_layout
from ada.ui.components.state_wrapper import (
    ComponentCover,
    build_safe_state_wrapper,
    build_state_wrapper,
)
from ada.ui.framework.core import ready_attributes

register_page(__name__, path='/', name='Inicio')


def _broken_component():
    raise RuntimeError('Reference component failure')


_catalog = build_reference_dashboard_catalog()
_io_dashboard = _catalog.dashboard('integrated_operations')
_process_mounts = {
    tool_key: dashboard.mount()
    for tool_key, dashboard in _catalog.dashboards.items()
    if tool_key != 'integrated_operations'
}

layout = html.Div(
    [
        html.H1('ADA UI Reference'),
        html.P('Estados, layouts y alarmas interactivas de referencia para ADA.'),
        html.Div(
            className='reference-ada__resilience-grid',
            children=[
                build_state_wrapper(
                    content=html.Div('Contenido stale', className='reference-ada__demo-content'),
                    cover=ComponentCover.stale(),
                ),
                build_state_wrapper(
                    content=html.Div(
                        'Contenido de fuente',
                        className='reference-ada__demo-content',
                    ),
                    cover=ComponentCover.source_error(),
                ),
                build_state_wrapper(
                    content=html.Div('Módulo futuro', className='reference-ada__demo-content'),
                    cover=ComponentCover.construction(),
                ),
                build_safe_state_wrapper(
                    build_content=_broken_component,
                ),
            ],
        ),
        html.Section(
            [
                html.H2('Dashboard E2E'),
                html.P(
                    'FakeSnapshotRepository → microcaché por worker → polling → Stores → '
                    'ComponentBundle → renderers de IO y Process.'
                ),
            ],
            className='reference-ada__dashboard-e2e-intro',
        ),
        build_reference_integrated_operations_layout(mount=_io_dashboard.mount()),
        build_reference_process_layout(mounts=_process_mounts),
        build_reference_alarm_interaction(),
    ],
    className='reference-ada__page',
    **ready_attributes('page-content', ready=True),
)
