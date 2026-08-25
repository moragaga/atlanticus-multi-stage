from datetime import UTC, datetime

from ada.configuration.tools import ToolConfigurationProjection
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from ada.runtime.component_stores import (
    build_runtime_component_store_mount,
    build_runtime_component_store_registry,
)

projection = ToolConfigurationProjection.create(
    source_revision='poc-source',
    projected_by='poc',
    projected_at_utc=datetime.now(UTC),
    manifest=INTEGRATED_OPERATIONS_MANIFEST,
)
registry = build_runtime_component_store_registry(projection)
mount = build_runtime_component_store_mount(registry)

print(f'tool: {registry.tool_key}')
print(f'components: {len(registry.components)}')
print(f'stores: {len(mount.stores)}')
for component in registry.components:
    print(
        f'{component.component_key}: '
        f'latest={component.latest_store_id} '
        f'timeseries={component.timeseries_store_id}'
    )
