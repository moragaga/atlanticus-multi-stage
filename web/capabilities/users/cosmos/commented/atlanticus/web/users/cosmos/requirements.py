from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
# Requirement declarativo que luego la composición traduce al provisioner transversal de Cosmos.
class UsersCosmosContainerRequirement:
    container_name: str
    partition_key: str
    ttl_seconds: int | None = None


# Users declara solo la infraestructura que consume hoy; user_activity se añadirá cuando exista esa capability.
USERS_COSMOS_REQUIREMENTS = (
    UsersCosmosContainerRequirement(
        container_name='users',
        partition_key='/partition_key',
    ),
    UsersCosmosContainerRequirement(
        container_name='users_support',
        partition_key='/partition_key',
    ),
)
