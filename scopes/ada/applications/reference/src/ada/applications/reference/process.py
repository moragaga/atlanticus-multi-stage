from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from dash import html

from ada.contracts.tool_manifest import (
    ProcessBodySection,
    ToolManifest,
    ToolScope,
    ToolSection,
    ToolSectionKind,
    ToolSource,
    ToolSourceKey,
    ToolTarget,
    build_process_manifest,
)
from ada.features.dashboard import DashboardMount
from ada.ui.components.component_card import build_component_card
from ada.ui.layouts.process import build_process_layout

_KPI = frozenset({ToolTarget.KPI})
_ALARM = frozenset({ToolTarget.ALARM})
_KPI_ALARM = frozenset({ToolTarget.KPI, ToolTarget.ALARM})
_SCOPE = ToolScope.PLANT
_PI = ToolSource(ToolSourceKey.PI, stale_after_seconds=300)

_CENTER_RIGHT = (
    (
        'planta_molibdeno',
        'Planta Molibdeno',
        ProcessBodySection.CENTER,
        (
            ('rougher', 'Rougher'),
            ('cleaner', 'Cleaner'),
            ('concentrado_molibdeno', 'Concentrado Molibdeno'),
        ),
    ),
    (
        'aguas_abajo',
        'Aguas Abajo',
        ProcessBodySection.RIGHT,
        (('stc', 'STC'), ('plf', 'PLF')),
    ),
)

_LEFT_CENTER_RIGHT = (
    (
        'aguas_arriba',
        'Aguas Arriba',
        ProcessBodySection.LEFT,
        (
            ('flotacion_colectiva', 'Flotación Colectiva'),
            ('tendencias_courier', 'Tendencias Courier'),
        ),
    ),
    (
        'planta_molibdeno',
        'Planta Molibdeno',
        ProcessBodySection.CENTER,
        (('principal', 'Planta Molibdeno'),),
    ),
    (
        'aguas_abajo',
        'Aguas Abajo',
        ProcessBodySection.RIGHT,
        (('stc', 'STC'), ('plf', 'PLF')),
    ),
)

_LEFT_CENTER_RIGHT_BOTTOM = (
    *_LEFT_CENTER_RIGHT,
    (
        'graficas_tendencia',
        'Gráficas Tendencia',
        ProcessBodySection.BOTTOM,
        (('graficas', 'Gráficas'),),
    ),
)


@dataclass(frozen=True, slots=True)
class ReferenceProcessVariant:
    title: str
    manifest: ToolManifest
    layout_id: str


_VARIANT_SPECS = (
    (
        'CENTER + RIGHT · CENTER con múltiples cards',
        'process_center_right_reference',
        'reference-process-center-right',
        _CENTER_RIGHT,
    ),
    (
        'LEFT + CENTER + RIGHT · CENTER con una card',
        'process_full_reference',
        'reference-process-full',
        _LEFT_CENTER_RIGHT,
    ),
    (
        'LEFT + CENTER + RIGHT + BOTTOM · CENTER y BOTTOM con una card',
        'process_full_bottom_reference',
        'reference-process-full-bottom',
        _LEFT_CENTER_RIGHT_BOTTOM,
    ),
)


def reference_process_variants() -> tuple[ReferenceProcessVariant, ...]:
    return tuple(
        ReferenceProcessVariant(
            title=title,
            manifest=_build_manifest(tool_key=tool_key, definitions=definitions),
            layout_id=layout_id,
        )
        for title, tool_key, layout_id, definitions in _VARIANT_SPECS
    )


def build_reference_process_layout(
    *,
    mounts: Mapping[str, DashboardMount] | None = None,
) -> html.Section:
    resolved_mounts = dict(mounts or {})
    return html.Section(
        [
            html.H2('Process Layout'),
            html.P(
                'Tres composiciones contractuales: CENTER+RIGHT = 10/2, '
                'LEFT+CENTER+RIGHT = 2/8/2 y la misma composición con BOTTOM = 12.'
            ),
            *(
                _build_variant(
                    variant,
                    mount=resolved_mounts.get(variant.manifest.tool_key),
                )
                for variant in reference_process_variants()
            ),
        ],
        className='reference-ada__process-layout-demo',
    )


def _build_variant(
    variant: ReferenceProcessVariant,
    *,
    mount: DashboardMount | None = None,
) -> html.Div:
    content = {
        component.key: _build_component_cards(
            variant.manifest,
            component.key,
            mount=mount,
        )
        for component in variant.manifest.children('body')
    }
    children = [
        html.H3(variant.title),
        build_process_layout(
            variant.manifest,
            component_content=content,
            layout_id=variant.layout_id,
        ),
    ]
    if mount is not None:
        children.append(mount.runtime_host())
    return html.Div(
        children,
        className='reference-ada__process-layout-variant',
    )


def _build_manifest(*, tool_key: str, definitions: tuple) -> ToolManifest:
    components = tuple(
        _component(
            key=key,
            display_name=display_name,
            role=role,
        )
        for key, display_name, role, _ in definitions
    )
    subcomponents = tuple(
        _subcomponent(
            component=component_key,
            subcomponent=subcomponent_key,
            display_name=display_name,
            alarm=role is ProcessBodySection.CENTER,
        )
        for component_key, _, role, cards in definitions
        for subcomponent_key, display_name in cards
    )
    return build_process_manifest(
        tool_key=tool_key,
        display_name='Process Reference',
        sources=(_PI,),
        operational_scope=_SCOPE,
        body_sections=(*components, *subcomponents),
    )


def _component(
    *,
    key: str,
    display_name: str,
    role: ProcessBodySection,
) -> ToolSection:
    return ToolSection(
        key=key,
        display_name=display_name,
        kind=ToolSectionKind.COMPONENT,
        scope=_SCOPE,
        parent_key='body',
        targets=_KPI_ALARM if role is ProcessBodySection.CENTER else _KPI,
        layout_role=role,
    )


def _subcomponent(
    *,
    component: str,
    subcomponent: str,
    display_name: str,
    alarm: bool,
) -> ToolSection:
    return ToolSection(
        component=component,
        subcomponent=subcomponent,
        display_name=display_name,
        kind=ToolSectionKind.SUBCOMPONENT,
        scope=_SCOPE,
        targets=_ALARM if alarm else (),
    )


def _build_component_cards(
    manifest: ToolManifest,
    component_key: str,
    *,
    mount: DashboardMount | None,
) -> html.Div:
    cards = []
    for section in manifest.children(component_key):
        if section.subcomponent is None:
            continue
        slot = mount.slot(component_key, section.subcomponent) if mount is not None else None
        cards.append(
            build_component_card(
                manifest,
                component=component_key,
                subcomponent=section.subcomponent,
                content=(
                    slot.content
                    if slot is not None
                    else html.Div(
                        'Contenido inyectado',
                        className='reference-ada__component-card-content',
                    )
                ),
                label=section.display_name,
                overlay=slot.overlay if slot is not None else None,
                class_name='flex-fill',
            )
        )
    return html.Div(cards, className='d-flex flex-column gap-1')
