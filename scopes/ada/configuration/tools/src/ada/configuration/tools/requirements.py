from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolCosmosContainerRequirement:
    container_name: str
    partition_key: str
    ttl_seconds: int | None = None


TOOL_COSMOS_REQUIREMENTS = (
    ToolCosmosContainerRequirement(
        container_name='configuration',
        partition_key='/partition_key',
    ),
)
