from __future__ import annotations

from ada.configuration.tools.errors import ToolConfigurationValidationError
from ada.configuration.tools.models import (
    ToolComponentConfiguration,
    ToolConfiguration,
    ToolConfigurationCatalog,
    ToolConfigurationKind,
)
from ada.contracts.tool_manifest import (
    ProcessBodySection,
    ToolManifest,
    ToolManifestError,
    ToolManifestRegistry,
    ToolScope,
    ToolSection,
    ToolSectionKind,
    ToolSource,
    ToolTarget,
    build_process_manifest,
)

_KPI = frozenset({ToolTarget.KPI})
_ALARM = frozenset({ToolTarget.ALARM})
_KPI_ALARM = frozenset({ToolTarget.KPI, ToolTarget.ALARM})
_OPERATIONAL_SCOPES = frozenset({ToolScope.MINE, ToolScope.PLANT})


def build_tool_manifest(configuration: ToolConfiguration) -> ToolManifest:
    try:
        if configuration.kind is ToolConfigurationKind.INTEGRATED_OPERATIONS:
            return _build_integrated_operations_manifest(configuration)
        if configuration.kind is ToolConfigurationKind.PROCESS:
            return _build_process_configuration_manifest(configuration)
    except ToolManifestError as error:
        raise ToolConfigurationValidationError(str(error)) from error
    raise ToolConfigurationValidationError('Tool kind is not supported')


def build_tool_manifest_registry(catalog: ToolConfigurationCatalog) -> ToolManifestRegistry:
    if not catalog.tools:
        raise ToolConfigurationValidationError('Tool catalog requires at least one tool')
    return ToolManifestRegistry(tuple(build_tool_manifest(tool) for tool in catalog.tools))


def _build_integrated_operations_manifest(configuration: ToolConfiguration) -> ToolManifest:
    if configuration.operational_scope is not None:
        raise ToolConfigurationValidationError(
            'Integrated operations cannot declare an operational scope'
        )
    sources = _build_sources(configuration)
    if not configuration.components:
        raise ToolConfigurationValidationError(
            'Integrated operations requires at least one component'
        )
    for component in configuration.components:
        _validate_integrated_operations_component(component)
    body_sections = _build_integrated_operations_body_sections(configuration)
    return ToolManifest(
        tool_key=configuration.tool_key,
        display_name=configuration.display_name,
        sources=sources,
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
                scope=ToolScope.GLOBAL,
                parent_key='header',
                targets=_KPI,
            ),
            ToolSection(
                component='global_indicators',
                subcomponent='mine',
                display_name='Indicadores Globales Mina',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=ToolScope.MINE,
                targets=_KPI,
            ),
            ToolSection(
                component='global_indicators',
                subcomponent='plant',
                display_name='Indicadores Globales Planta',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=ToolScope.PLANT,
                targets=_KPI,
            ),
            ToolSection(
                key='alarm_management',
                display_name='Gestión de Alarmas',
                kind=ToolSectionKind.COMPONENT,
                scope=ToolScope.GLOBAL,
                parent_key='header',
            ),
            ToolSection(
                component='alarm_management',
                subcomponent='mine',
                display_name='Gestión de Alarmas Mina',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=ToolScope.MINE,
            ),
            ToolSection(
                component='alarm_management',
                subcomponent='plant',
                display_name='Gestión de Alarmas Planta',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=ToolScope.PLANT,
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
                targets=_KPI,
            ),
            ToolSection(
                key='body',
                display_name='Contenido',
                kind=ToolSectionKind.REGION,
                scope=ToolScope.GLOBAL,
            ),
            ToolSection(
                key='mine',
                display_name='Mina',
                kind=ToolSectionKind.REGION,
                scope=ToolScope.MINE,
                parent_key='body',
            ),
            *tuple(section for section in body_sections if section.scope is ToolScope.MINE),
            ToolSection(
                key='plant',
                display_name='Planta',
                kind=ToolSectionKind.REGION,
                scope=ToolScope.PLANT,
                parent_key='body',
            ),
            *tuple(section for section in body_sections if section.scope is ToolScope.PLANT),
        ),
    )


def _build_integrated_operations_body_sections(
    configuration: ToolConfiguration,
) -> list[ToolSection]:
    result: list[ToolSection] = []
    for scope in (ToolScope.MINE, ToolScope.PLANT):
        components = tuple(
            component for component in configuration.components if component.scope is scope
        )
        positions = {component.key: index for index, component in enumerate(components)}
        deferred: dict[int, list[ToolSection]] = {}
        for index, component in enumerate(components):
            result.append(
                ToolSection(
                    key=component.key,
                    display_name=component.display_name,
                    kind=ToolSectionKind.COMPONENT,
                    scope=scope,
                    parent_key=scope.value,
                    targets=_KPI_ALARM,
                )
            )
            for subcomponent in component.subcomponents:
                section = ToolSection(
                    component=component.key,
                    subcomponent=subcomponent.key,
                    display_name=subcomponent.display_name,
                    kind=ToolSectionKind.SUBCOMPONENT,
                    scope=scope,
                    targets=_ALARM,
                    linked_component_keys=subcomponent.linked_component_keys,
                )
                if not subcomponent.linked_component_keys:
                    result.append(section)
                    continue
                try:
                    last_position = max(
                        positions[key]
                        for key in (component.key, *subcomponent.linked_component_keys)
                    )
                except KeyError as error:
                    raise ToolConfigurationValidationError(
                        f'Integrated operations shared subcomponent {subcomponent.key!r} '
                        'references an unknown component'
                    ) from error
                deferred.setdefault(last_position, []).append(section)
            result.extend(deferred.pop(index, ()))
    return result


def _build_process_configuration_manifest(configuration: ToolConfiguration) -> ToolManifest:
    if configuration.operational_scope not in _OPERATIONAL_SCOPES:
        raise ToolConfigurationValidationError(
            'Process requires mine or plant as operational scope'
        )
    if not configuration.components:
        raise ToolConfigurationValidationError('Process requires at least one component')
    roles = tuple(component.layout_role for component in configuration.components)
    if any(role is None for role in roles):
        raise ToolConfigurationValidationError('Process components require a layout role')
    if len(roles) != len(set(roles)):
        raise ToolConfigurationValidationError('Process component layout roles must be unique')
    if ProcessBodySection.CENTER not in roles:
        raise ToolConfigurationValidationError('Process requires a center component')
    body_sections: list[ToolSection] = []
    for component in configuration.components:
        _validate_process_component(component)
        role = component.layout_role
        if role is None:
            raise ToolConfigurationValidationError('Process component layout role is required')
        targets = _KPI_ALARM if role is ProcessBodySection.CENTER else _KPI
        body_sections.append(
            ToolSection(
                key=component.key,
                display_name=component.display_name,
                kind=ToolSectionKind.COMPONENT,
                scope=configuration.operational_scope,
                parent_key='body',
                targets=targets,
                layout_role=role,
            )
        )
        for subcomponent in component.subcomponents:
            body_sections.append(
                ToolSection(
                    component=component.key,
                    subcomponent=subcomponent.key,
                    display_name=subcomponent.display_name,
                    kind=ToolSectionKind.SUBCOMPONENT,
                    scope=configuration.operational_scope,
                    targets=_ALARM if role is ProcessBodySection.CENTER else (),
                )
            )
    return build_process_manifest(
        tool_key=configuration.tool_key,
        display_name=configuration.display_name,
        sources=_build_sources(configuration),
        operational_scope=configuration.operational_scope,
        body_sections=body_sections,
    )


def _build_sources(configuration: ToolConfiguration) -> tuple[ToolSource, ...]:
    if not configuration.sources:
        raise ToolConfigurationValidationError('Tool requires at least one source')
    return tuple(
        ToolSource(
            key=source.key,
            stale_after_seconds=source.stale_after_seconds,
        )
        for source in configuration.sources
    )


def _validate_integrated_operations_component(component: ToolComponentConfiguration) -> None:
    if component.scope not in _OPERATIONAL_SCOPES:
        raise ToolConfigurationValidationError(
            f'Integrated operations component {component.key!r} requires mine or plant scope'
        )
    if component.layout_role is not None:
        raise ToolConfigurationValidationError(
            'Integrated operations components cannot declare a layout role'
        )
    if not component.subcomponents:
        raise ToolConfigurationValidationError(
            f'Integrated operations component {component.key!r} requires at least one subcomponent'
        )


def _validate_process_component(component: ToolComponentConfiguration) -> None:
    if component.scope is not None:
        raise ToolConfigurationValidationError('Process components inherit the tool scope')
    if component.layout_role is None:
        raise ToolConfigurationValidationError('Process components require a layout role')
    if not component.subcomponents:
        raise ToolConfigurationValidationError(
            f'Process component {component.key!r} requires at least one subcomponent'
        )
    if any(item.linked_component_keys for item in component.subcomponents):
        raise ToolConfigurationValidationError(
            'Process subcomponents cannot link to other components'
        )
