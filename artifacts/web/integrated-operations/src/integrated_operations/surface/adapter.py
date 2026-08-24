from __future__ import annotations

from dataclasses import dataclass

from ada.compositions.integrated_operations import (
    IntegratedOperationsCompositionError,
    create_integrated_operations_tool_modules,
)
from ada.compositions.surface import AdaSurfaceAdapterError, AdaSurfaceComposition
from ada.contracts.tool_manifest import ToolManifest
from ada.runtime.web import SharedSnapshotReader
from integrated_operations.runtime.snapshots import IntegratedOperationsSnapshotRepository
from integrated_operations.tool import (
    build_integrated_operations_composition,
    build_integrated_operations_tool,
)


@dataclass(frozen=True, slots=True)
class IntegratedOperationsSurfaceAdapter:
    key: str = 'integrated_operations'

    def supports(self, manifest: ToolManifest) -> bool:
        return manifest.tool_key == self.key

    def compose(self, manifest: ToolManifest) -> AdaSurfaceComposition:
        try:
            composition = build_integrated_operations_composition(manifest)
        except IntegratedOperationsCompositionError as error:
            raise AdaSurfaceAdapterError(
                'Integrated Operations manifest is not compatible'
            ) from error
        snapshot_reader = SharedSnapshotReader(
            IntegratedOperationsSnapshotRepository(composition.dashboard),
            ttl_seconds=1.0,
        )
        return AdaSurfaceComposition(
            adapter_key=self.key,
            manifest=manifest,
            modules=create_integrated_operations_tool_modules(
                composition,
                snapshot_reader=snapshot_reader,
            ),
            builder=lambda _services: build_integrated_operations_tool(composition),
        )
