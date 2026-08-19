from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolCosmosContainerRequirement:
    # Contrato físico mínimo del contenedor que necesita Tools.
    container_name: str
    partition_key: str
    ttl_seconds: int | None = None


# Tools comparte el contenedor de configuración mediante una partition key genérica.
TOOL_COSMOS_REQUIREMENTS = (
    ToolCosmosContainerRequirement(
        container_name='configuration',
        partition_key='/partition_key',
    ),
)
