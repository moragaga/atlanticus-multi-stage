from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UsersCosmosContainerRequirement:
    container_name: str
    partition_key: str
    ttl_seconds: int | None = None


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
