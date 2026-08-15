from collections.abc import Iterable

from ..enums import ProcessBodySection, ToolScope, ToolSectionKind, ToolTarget
from ..errors import ToolManifestError
from ..models import ToolManifest, ToolSection, ToolSource

_KPI = frozenset({ToolTarget.KPI})
_ALARM = frozenset({ToolTarget.ALARM})
_KPI_ALARM = frozenset({ToolTarget.KPI, ToolTarget.ALARM})
_PROCESS_SCOPES = frozenset({ToolScope.MINE, ToolScope.PLANT})


def build_process_manifest(
    *,
    tool_key: str,
    display_name: str,
    sources: Iterable[ToolSource],
    operational_scope: ToolScope,
    body_sections: Iterable[ToolSection],
) -> ToolManifest:
    if operational_scope not in _PROCESS_SCOPES:
        raise ToolManifestError('Process operational_scope must be mine or plant')

    resolved_sections = tuple(body_sections)
    if not resolved_sections:
        raise ToolManifestError('Process manifest requires at least one body section')

    _validate_process_section_declarations(
        sections=resolved_sections,
        operational_scope=operational_scope,
    )

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
    if any(section.scope is not operational_scope for section in sections):
        raise ToolManifestError('Process body section scope must match operational_scope')

    regions = tuple(section for section in sections if section.parent_key == 'body')
    if not regions:
        raise ToolManifestError('Process manifest requires at least one body region')
    if any(section.kind is not ToolSectionKind.REGION for section in regions):
        raise ToolManifestError('Process body direct children must be regions')
    if any(section.layout_role is None for section in regions):
        raise ToolManifestError('Process body regions require a layout_role')

    roles = tuple(section.layout_role for section in regions)
    if len(roles) != len(set(roles)):
        raise ToolManifestError('Process manifest contains duplicate layout roles')
    if ProcessBodySection.CENTER not in roles:
        raise ToolManifestError('Process manifest requires the center layout role')

    for region in regions:
        expected_targets = _KPI_ALARM if region.layout_role is ProcessBodySection.CENTER else _KPI
        if region.targets != expected_targets:
            raise ToolManifestError(
                f'Process region {region.key!r} has invalid targets for its layout role'
            )


def _validate_process_manifest_body(manifest: ToolManifest) -> None:
    center = manifest.region_for_layout_role(ProcessBodySection.CENTER)
    body_children = manifest.children('body')
    body_region_keys = {section.key for section in body_children}

    for section in manifest.sections:
        if section.key in body_region_keys or section.key in {
            'header',
            'global_indicators',
            'alarm_management',
            'alarm_status',
            'time_status',
            'body',
        }:
            continue
        path = manifest.path(section.key)
        if len(path) < 3 or path[0].key != 'body' or path[1].key != center.key:
            raise ToolManifestError('Only the center process region can declare child sections')
        if section.kind not in {ToolSectionKind.COMPONENT, ToolSectionKind.SUBCOMPONENT}:
            raise ToolManifestError('Process center children must be components or subcomponents')
        if section.targets != _ALARM:
            raise ToolManifestError('Process center child sections must accept only alarm targets')
