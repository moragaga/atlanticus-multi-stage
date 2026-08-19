from __future__ import annotations
# Espejo pedagógico: la actividad vigente es efímera y declara TTL de veinticuatro horas.

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserActivityCosmosContainerRequirement:
    container_name: str
    partition_key: str
    ttl_seconds: int


USER_ACTIVITY_COSMOS_REQUIREMENTS = (
    UserActivityCosmosContainerRequirement(
        container_name='user_activity',
        partition_key='/id',
        ttl_seconds=86_400,
    ),
)
