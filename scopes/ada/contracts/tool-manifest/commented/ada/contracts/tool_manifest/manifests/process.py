# Espejo comentado: conserva exactamente la lógica productiva del módulo.
# Los comentarios describen la responsabilidad sin alterar el AST ejecutable.
from collections.abc import Iterable

from ..enums import ProcessBodySection, ToolScope, ToolSectionKind, ToolTarget
from ..errors import ToolManifestError
from ..models import ToolManifest, ToolSection

_KPI = frozenset({ToolTarget.KPI})
_KPI_ALARM = frozenset({ToolTarget.KPI, ToolTarget.ALARM})
_PROCESS_SCOPES = frozenset({ToolScope.MINE, ToolScope.PLANT})


def build_process_manifest(
    *,
    tool_key: str,
    display_name: str,
    operational_scope: ToolScope,
    body_sections: Iterable[ProcessBodySection],
) -> ToolManifest:
    if operational_scope not in _PROCESS_SCOPES:
        raise ToolManifestError('Process operational_scope must be mine or plant')

    resolved_sections = tuple(body_sections)
    if not resolved_sections:
        raise ToolManifestError('Process manifest requires at least one body section')
    if len(resolved_sections) != len(set(resolved_sections)):
        raise ToolManifestError('Process manifest contains duplicate body sections')
    if ProcessBodySection.CENTER not in resolved_sections:
        raise ToolManifestError('Process manifest requires the center section')

    return ToolManifest(
        tool_key=tool_key,
        display_name=display_name,
        sections=(
            ToolSection('header', 'Header', ToolSectionKind.REGION, ToolScope.GLOBAL),
            ToolSection(
                'global_indicators',
                'Indicadores Globales',
                ToolSectionKind.COMPONENT,
                operational_scope,
                parent_key='header',
                targets=_KPI,
            ),
            ToolSection(
                'alarm_management',
                'Gestión de Alarmas',
                ToolSectionKind.COMPONENT,
                operational_scope,
                parent_key='header',
            ),
            ToolSection(
                'alarm_status',
                'Estado de Alarmas',
                ToolSectionKind.COMPONENT,
                ToolScope.GLOBAL,
                parent_key='header',
            ),
            ToolSection(
                'time_status',
                'Estado Temporal',
                ToolSectionKind.COMPONENT,
                ToolScope.GLOBAL,
            ),
            ToolSection('body', 'Contenido', ToolSectionKind.REGION, operational_scope),
            *(
                _build_process_body_section(section, operational_scope=operational_scope)
                for section in resolved_sections
            ),
        ),
    )


def _build_process_body_section(
    section: ProcessBodySection,
    *,
    operational_scope: ToolScope,
) -> ToolSection:
    targets = _KPI_ALARM if section is ProcessBodySection.CENTER else _KPI
    return ToolSection(
        key=section.value,
        display_name=_display_name(section),
        kind=ToolSectionKind.COMPONENT,
        scope=operational_scope,
        parent_key='body',
        targets=targets,
    )


def _display_name(section: ProcessBodySection) -> str:
    return {
        ProcessBodySection.LEFT: 'Izquierda',
        ProcessBodySection.CENTER: 'Centro',
        ProcessBodySection.RIGHT: 'Derecha',
        ProcessBodySection.BOTTOM: 'Inferior',
    }[section]
