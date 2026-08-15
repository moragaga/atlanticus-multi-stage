from collections.abc import Iterable

from ..enums import ProcessBodySection, ToolScope, ToolSectionKind, ToolTarget
from ..errors import ToolManifestError
from ..models import ToolManifest, ToolSection, ToolSource

_KPI = frozenset({ToolTarget.KPI})
_ALARM = frozenset({ToolTarget.ALARM})
_KPI_ALARM = frozenset({ToolTarget.KPI, ToolTarget.ALARM})
_PROCESS_SCOPES = frozenset({ToolScope.MINE, ToolScope.PLANT})
_FIXED_SECTION_KEYS = frozenset(
    {
        'header',
        'global_indicators',
        'alarm_management',
        'alarm_status',
        'time_status',
        'body',
    }
)


def build_process_manifest(
    *,
    tool_key: str,
    display_name: str,
    sources: Iterable[ToolSource],
    operational_scope: ToolScope,
    body_sections: Iterable[ToolSection],
) -> ToolManifest:
    # Process solo puede operar sobre el scope minero o planta, nunca GLOBAL.
    if operational_scope not in _PROCESS_SCOPES:
        raise ToolManifestError('Process operational_scope must be mine or plant')

    # La herramienta declara sus componentes funcionales y las cards que cuelgan de ellos.
    resolved_sections = tuple(body_sections)
    if not resolved_sections:
        raise ToolManifestError('Process manifest requires at least one body section')

    _validate_process_section_declarations(
        sections=resolved_sections,
        operational_scope=operational_scope,
    )

    # Las secciones transversales son comunes; body contiene directamente los componentes Process.
    manifest = ToolManifest(
        tool_key=tool_key,
        display_name=display_name,
        sources=tuple(sources),
        sections=(
            ToolSection(
                key='header',
                display_name='Header',
                kind=ToolSectionKind.REGION,
                scope=ToolScope.GLOBAL,
            ),
            ToolSection(
                key='global_indicators',
                display_name='Indicadores Globales',
                kind=ToolSectionKind.COMPONENT,
                scope=operational_scope,
                parent_key='header',
                targets=_KPI_ALARM,
            ),
            ToolSection(
                key='alarm_management',
                display_name='Gestión de Alarmas',
                kind=ToolSectionKind.COMPONENT,
                scope=operational_scope,
                parent_key='header',
            ),
            ToolSection(
                key='alarm_status',
                display_name='Estado de Alarmas',
                kind=ToolSectionKind.COMPONENT,
                scope=ToolScope.GLOBAL,
                parent_key='header',
            ),
            ToolSection(
                key='time_status',
                display_name='Estado Temporal',
                kind=ToolSectionKind.COMPONENT,
                scope=ToolScope.GLOBAL,
                targets=_KPI_ALARM,
            ),
            ToolSection(
                key='body',
                display_name='Contenido',
                kind=ToolSectionKind.REGION,
                scope=operational_scope,
            ),
            *resolved_sections,
        ),
    )
    _validate_process_manifest_body(manifest)
    return manifest


def _validate_process_section_declarations(
    *,
    sections: tuple[ToolSection, ...],
    operational_scope: ToolScope,
) -> None:
    # Todo el body Process pertenece al mismo scope operacional de la herramienta.
    if any(section.scope is not operational_scope for section in sections):
        raise ToolManifestError('Process body section scope must match operational_scope')

    # LEFT/CENTER/RIGHT/BOTTOM son roles del componente, no regiones persistidas adicionales.
    components = tuple(section for section in sections if section.parent_key == 'body')
    if not components:
        raise ToolManifestError('Process manifest requires at least one body component')
    if any(section.kind is not ToolSectionKind.COMPONENT for section in components):
        raise ToolManifestError('Process body direct children must be components')
    if any(section.layout_role is None for section in components):
        raise ToolManifestError('Process body components require a layout_role')

    roles = tuple(section.layout_role for section in components)
    if len(roles) != len(set(roles)):
        raise ToolManifestError('Process manifest contains duplicate layout roles')
    if ProcessBodySection.CENTER not in roles:
        raise ToolManifestError('Process manifest requires the center layout role')

    # KPI se configura por componente; CENTER además es target directo de alarmas.
    for component in components:
        expected_targets = (
            _KPI_ALARM if component.layout_role is ProcessBodySection.CENTER else _KPI
        )
        if component.targets != expected_targets:
            raise ToolManifestError(
                f'Process component {component.key!r} has invalid targets for its layout role'
            )


def _validate_process_manifest_body(manifest: ToolManifest) -> None:
    components = manifest.children('body')
    component_keys = {component.key for component in components}

    # Cada componente expone una o más ComponentCards; BOTTOM es deliberadamente una sola card.
    for component in components:
        children = manifest.children(component.key)
        if not children:
            raise ToolManifestError(
                f'Process component {component.key!r} requires at least one subcomponent'
            )
        if any(child.kind is not ToolSectionKind.SUBCOMPONENT for child in children):
            raise ToolManifestError(
                f'Process component {component.key!r} children must be subcomponents'
            )
        if component.layout_role is ProcessBodySection.BOTTOM and len(children) != 1:
            raise ToolManifestError('Process bottom component requires exactly one subcomponent')

    # Solo las cards del componente CENTER son divisibles para alarmas.
    for section in manifest.sections:
        if section.key in _FIXED_SECTION_KEYS or section.key in component_keys:
            continue

        path = manifest.path(section.key)
        if len(path) != 3 or path[0].key != 'body' or path[1].key not in component_keys:
            raise ToolManifestError('Process body must follow COMPONENT -> SUBCOMPONENT')

        component = path[1]
        expected_targets = (
            _ALARM if component.layout_role is ProcessBodySection.CENTER else frozenset()
        )
        if section.targets != expected_targets:
            if component.layout_role is ProcessBodySection.CENTER:
                raise ToolManifestError(
                    'Process center subcomponents must accept only alarm targets'
                )
            raise ToolManifestError('Process non-center subcomponents cannot declare targets')
