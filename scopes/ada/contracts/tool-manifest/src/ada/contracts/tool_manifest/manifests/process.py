from collections.abc import Iterable

from ..enums import ProcessBodySection, ToolScope, ToolSectionKind, ToolTarget
from ..errors import ToolManifestError
from ..models import ToolManifest, ToolSection

_KPI = frozenset({ToolTarget.KPI})
_KPI_ALARM = frozenset({ToolTarget.KPI, ToolTarget.ALARM})


def build_process_manifest(
    *,
    tool_key: str,
    display_name: str,
    body_sections: Iterable[ProcessBodySection],
) -> ToolManifest:
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
            ToolSection('header', 'Header', ToolSectionKind.REGION, ToolScope.PROCESS),
            ToolSection(
                'global_indicators',
                'Indicadores Globales',
                ToolSectionKind.COMPONENT,
                ToolScope.PROCESS,
                parent_key='header',
                targets=_KPI,
            ),
            ToolSection(
                'alarm_management',
                'Gestión de Alarmas',
                ToolSectionKind.COMPONENT,
                ToolScope.PROCESS,
                parent_key='header',
            ),
            ToolSection(
                'alarm_status',
                'Estado de Alarmas',
                ToolSectionKind.COMPONENT,
                ToolScope.PROCESS,
                parent_key='header',
            ),
            ToolSection(
                'time_status',
                'Estado Temporal',
                ToolSectionKind.COMPONENT,
                ToolScope.PROCESS,
            ),
            ToolSection('body', 'Contenido', ToolSectionKind.REGION, ToolScope.PROCESS),
            *(_build_process_body_section(section) for section in resolved_sections),
        ),
    )


def _build_process_body_section(section: ProcessBodySection) -> ToolSection:
    targets = _KPI_ALARM if section is ProcessBodySection.CENTER else _KPI
    return ToolSection(
        key=section.value,
        display_name=_display_name(section),
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.PROCESS,
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
