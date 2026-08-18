# Espejo pedagógico: este archivo conserva exactamente la lógica del código productivo.
# Configuración de herramientas del scope ADA. Convierte datos administrativos mínimos en contratos runtime ToolManifest sin acoplar el dominio a la UI.
# Los comentarios explican la intención arquitectónica; no agregan ramas, estado ni comportamiento.

from ada.configuration.tools.models import (
    ToolComponentConfiguration,
    ToolConfiguration,
    ToolConfigurationKind,
    ToolSourceConfiguration,
    ToolSubcomponentConfiguration,
)
from ada.contracts.tool_manifest import ToolManifest, ToolSectionKind


def integrated_operations_configuration_from_manifest(
    manifest: ToolManifest,
) -> ToolConfiguration:
    components = []
    for scope_key in ('mine', 'plant'):
        scope = manifest.section(scope_key).scope
        for section in manifest.children(scope_key):
            if section.kind is not ToolSectionKind.COMPONENT:
                continue
            subcomponents = tuple(
                ToolSubcomponentConfiguration(
                    key=child.subcomponent or child.key,
                    display_name=child.display_name,
                    linked_component_keys=child.linked_component_keys,
                )
                for child in manifest.children(section.key)
                if child.kind is ToolSectionKind.SUBCOMPONENT
            )
            components.append(
                ToolComponentConfiguration(
                    key=section.key,
                    display_name=section.display_name,
                    scope=scope,
                    subcomponents=subcomponents,
                )
            )
    return ToolConfiguration(
        tool_key=manifest.tool_key,
        display_name=manifest.display_name,
        kind=ToolConfigurationKind.INTEGRATED_OPERATIONS,
        sources=tuple(
            ToolSourceConfiguration(
                key=source.key,
                stale_after_seconds=source.stale_after_seconds,
            )
            for source in manifest.sources
        ),
        components=tuple(components),
    )
