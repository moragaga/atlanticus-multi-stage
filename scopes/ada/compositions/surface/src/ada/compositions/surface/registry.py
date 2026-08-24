from __future__ import annotations

from dataclasses import dataclass

from ada.contracts.tool_manifest import ToolManifest

from .adapter import AdaSurfaceAdapter
from .errors import AdaSurfaceAdapterError, AdaSurfaceLookupError
from .models import AdaSurfaceComposition


@dataclass(frozen=True, slots=True)
class AdaSurfaceRegistry:
    adapters: tuple[AdaSurfaceAdapter, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'adapters', tuple(self.adapters))
        if not self.adapters:
            raise AdaSurfaceAdapterError('Surface registry requires at least one adapter')
        keys = tuple(adapter.key for adapter in self.adapters)
        if any(not key.strip() for key in keys):
            raise AdaSurfaceAdapterError('Surface adapter key cannot be empty')
        if len(keys) != len(set(keys)):
            raise AdaSurfaceAdapterError('Surface registry contains duplicate adapter keys')

    def resolve(self, manifest: ToolManifest) -> AdaSurfaceAdapter:
        matches = tuple(adapter for adapter in self.adapters if adapter.supports(manifest))
        if not matches:
            raise AdaSurfaceLookupError(
                f'No surface adapter supports tool manifest: {manifest.tool_key}'
            )
        if len(matches) > 1:
            keys = ', '.join(adapter.key for adapter in matches)
            raise AdaSurfaceLookupError(
                f'Multiple surface adapters support tool manifest {manifest.tool_key!r}: {keys}'
            )
        return matches[0]

    def compose(self, manifest: ToolManifest) -> AdaSurfaceComposition:
        adapter = self.resolve(manifest)
        composition = adapter.compose(manifest)
        if composition.adapter_key != adapter.key:
            raise AdaSurfaceAdapterError(
                f'Surface composition adapter key does not match registry adapter: {adapter.key}'
            )
        if composition.manifest != manifest:
            raise AdaSurfaceAdapterError(
                'Surface composition manifest does not match input manifest'
            )
        return composition
