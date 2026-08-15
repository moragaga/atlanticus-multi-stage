from dash import html

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
from ada.ui.layouts.process import build_process_layout

_KPI = frozenset({ToolTarget.KPI})
_KPI_ALARM = frozenset({ToolTarget.KPI, ToolTarget.ALARM})


def build_reference_process_layout() -> html.Section:
    # La referencia usa nombres reales del legacy visual, pero la geometría viene del rol genérico.
    manifest = _build_reference_process_manifest()
    content = {
        'aguas_arriba': _build_reference_stack(('Flotación Colectiva', 'Tendencias Courier')),
        'planta_molibdeno': _build_reference_card('Contenido central'),
        'aguas_abajo': _build_reference_stack(('STC', 'PLF')),
        'indicadores_inferiores': _build_reference_card('Bottom opcional'),
    }
    return html.Section(
        [
            html.H2('Process Layout'),
            html.P(
                'Ejemplo contractual con LEFT/CENTER/RIGHT = 2/8/2 y BOTTOM = 12; '
                'CENTER y BOTTOM son unidades únicas, mientras LEFT y RIGHT pueden apilar cards.'
            ),
            build_process_layout(
                manifest,
                region_content=content,
                layout_id='reference-process-layout',
            ),
        ],
        className='reference-ada__process-layout-demo',
    )


def _build_reference_process_manifest():
    scope = ToolScope.PLANT
    return build_process_manifest(
        tool_key='flotacion_selectiva_reference',
        display_name='Flotación Selectiva',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=300),),
        operational_scope=scope,
        body_sections=(
            _region('aguas_arriba', 'Aguas Arriba', scope, ProcessBodySection.LEFT),
            _region('planta_molibdeno', 'Planta Molibdeno', scope, ProcessBodySection.CENTER),
            _region('aguas_abajo', 'Aguas Abajo', scope, ProcessBodySection.RIGHT),
            _region(
                'indicadores_inferiores',
                'Indicadores Inferiores',
                scope,
                ProcessBodySection.BOTTOM,
            ),
        ),
    )


def _region(
    key: str,
    display_name: str,
    scope: ToolScope,
    role: ProcessBodySection,
) -> ToolSection:
    # Solo CENTER acepta alarmas; todas las regiones siguen siendo configurables para KPI.
    return ToolSection(
        key=key,
        display_name=display_name,
        kind=ToolSectionKind.REGION,
        scope=scope,
        parent_key='body',
        targets=_KPI_ALARM if role is ProcessBodySection.CENTER else _KPI,
        layout_role=role,
    )


def _build_reference_card(label: str) -> html.Div:
    # CENTER y BOTTOM se representan como una sola unidad visual inyectada.
    return html.Div(label, className='reference-ada__process-content-card flex-fill')


def _build_reference_stack(labels: tuple[str, ...]) -> html.Div:
    # LEFT y RIGHT pueden apilar varias cards; el layout no inspecciona su anatomía interna.
    return html.Div(
        [_build_reference_card(label) for label in labels],
        className='d-flex flex-column gap-1',
    )
