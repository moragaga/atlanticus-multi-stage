# Una composición de superficie encapsula manifest, módulos y builder sin conocer Operaciones Integradas o Procesos.
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from dash.development.base_component import Component

from ada.contracts.tool_manifest import ToolManifest
from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry

AdaSurfaceBuilder = Callable[[ServiceRegistry], Component]


@dataclass(frozen=True, slots=True)
class AdaSurfaceComposition:
    adapter_key: str
    manifest: ToolManifest
    modules: tuple[WebModule, ...]
    builder: AdaSurfaceBuilder

    def __post_init__(self) -> None:
        if not self.adapter_key.strip():
            raise ValueError('Surface adapter_key cannot be empty')
        object.__setattr__(self, 'modules', tuple(self.modules))

    def build(self, services: ServiceRegistry) -> Component:
        return self.builder(services)
