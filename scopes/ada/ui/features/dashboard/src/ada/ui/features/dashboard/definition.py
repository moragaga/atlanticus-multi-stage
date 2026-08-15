from __future__ import annotations

from dataclasses import dataclass

from ada.contracts.tool_manifest import ToolManifest, ToolSection, ToolSectionKind

from .errors import DashboardDefinitionError
from .models import (
    ComponentProjectionDefinition,
    ComponentRenderer,
    ComponentRendererRegistry,
    DashboardPollingSettings,
    DashboardToolConfiguration,
)


@dataclass(frozen=True, slots=True)
class DashboardComponentDefinition:
    section: ToolSection
    projection: ComponentProjectionDefinition | None
    renderer: ComponentRenderer | None

    @property
    def construction(self) -> bool:
        return self.renderer is None or self.projection is None

    @property
    def callback_required(self) -> bool:
        return self.renderer is not None and self.projection is not None


@dataclass(frozen=True, slots=True)
class DashboardDefinition:
    manifest: ToolManifest
    configuration: DashboardToolConfiguration
    components: tuple[DashboardComponentDefinition, ...]
    polling: DashboardPollingSettings | None = None

    @classmethod
    def build(
        cls,
        *,
        manifest: ToolManifest,
        configuration: DashboardToolConfiguration,
        renderers: ComponentRendererRegistry,
        polling: DashboardPollingSettings | None = None,
    ) -> DashboardDefinition:
        if not isinstance(manifest, ToolManifest):
            raise DashboardDefinitionError('Dashboard requires a ToolManifest')
        if not isinstance(configuration, DashboardToolConfiguration):
            raise DashboardDefinitionError('Dashboard requires DashboardToolConfiguration')
        if not isinstance(renderers, ComponentRendererRegistry):
            raise DashboardDefinitionError('Dashboard requires ComponentRendererRegistry')
        if polling is not None and not isinstance(polling, DashboardPollingSettings):
            raise DashboardDefinitionError('Dashboard polling must use DashboardPollingSettings')

        components = _body_components(manifest)
        component_keys = {section.key for section in components}
        _validate_projection_keys(configuration, component_keys)
        _validate_renderer_keys(renderers, component_keys)

        definitions = tuple(
            DashboardComponentDefinition(
                section=section,
                projection=configuration.projection(section.key),
                renderer=renderers.renderer(section.key),
            )
            for section in components
        )
        return cls(
            manifest=manifest,
            configuration=configuration,
            components=definitions,
            polling=polling,
        )

    def component(self, component_key: str) -> DashboardComponentDefinition:
        for component in self.components:
            if component.section.key == component_key:
                return component
        raise DashboardDefinitionError(f'Unknown dashboard component: {component_key!r}')


def _body_components(manifest: ToolManifest) -> tuple[ToolSection, ...]:
    try:
        body = manifest.section('body')
    except Exception as error:
        raise DashboardDefinitionError('Dashboard manifest requires body section') from error
    if body.kind is not ToolSectionKind.REGION:
        raise DashboardDefinitionError('Dashboard body section must be a region')

    resolved: list[ToolSection] = []
    pending = list(manifest.children(body.key))
    while pending:
        section = pending.pop(0)
        if section.kind is ToolSectionKind.COMPONENT:
            resolved.append(section)
            continue
        if section.kind is ToolSectionKind.REGION:
            pending[0:0] = manifest.children(section.key)
            continue
        raise DashboardDefinitionError('Dashboard body cannot contain direct subcomponents')
    if not resolved:
        raise DashboardDefinitionError('Dashboard body requires at least one component')
    return tuple(resolved)


def _validate_projection_keys(
    configuration: DashboardToolConfiguration,
    component_keys: set[str],
) -> None:
    unknown = tuple(
        item.component_key
        for item in configuration.components
        if item.component_key not in component_keys
    )
    if unknown:
        raise DashboardDefinitionError(
            f'Dashboard projection references unknown component: {unknown[0]!r}'
        )


def _validate_renderer_keys(
    renderers: ComponentRendererRegistry,
    component_keys: set[str],
) -> None:
    unknown = tuple(
        item.component_key
        for item in renderers.definitions
        if item.component_key not in component_keys
    )
    if unknown:
        raise DashboardDefinitionError(
            f'Dashboard renderer references unknown component: {unknown[0]!r}'
        )
