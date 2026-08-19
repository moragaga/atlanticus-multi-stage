# Espejo comentado: traduce requerimientos declarados por capabilities y ejecuta provisioning explícito fuera del lifecycle runtime.
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol

from atlanticus.connectivity.cosmos import (
    CosmosClient,
    CosmosContainerSpec,
    CosmosProvisioner,
    CosmosSettings,
)


class CosmosContainerRequirement(Protocol):
    container_name: str
    partition_key: str
    ttl_seconds: int | None


@dataclass(frozen=True, slots=True)
class CosmosProvisioningResult:
    databases_created: tuple[str, ...]
    containers_created: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'databases_created', tuple(self.databases_created))
        object.__setattr__(
            self,
            'containers_created',
            MappingProxyType(
                {
                    name: tuple(container_names)
                    for name, container_names in self.containers_created.items()
                }
            ),
        )


def create_cosmos_container_specs(
    requirements: Sequence[CosmosContainerRequirement],
) -> tuple[CosmosContainerSpec, ...]:
    if isinstance(requirements, str | bytes | bytearray | Mapping):
        raise TypeError('requirements must be a sequence')
    try:
        values = tuple(requirements)
    except TypeError:
        raise TypeError('requirements must be a sequence') from None
    if not values:
        raise ValueError('At least one Cosmos container requirement is required')

    specs = tuple(
        CosmosContainerSpec(
            name=requirement.container_name,
            partition_key_path=requirement.partition_key,
            default_ttl_seconds=requirement.ttl_seconds,
        )
        for requirement in values
    )
    names = tuple(spec.name for spec in specs)
    if len(names) != len(set(names)):
        raise ValueError('Cosmos container requirements must have unique container names')
    return specs


def ensure_cosmos_infrastructure(
    *,
    cosmos_connections: Mapping[str, CosmosSettings],
    requirements_by_connection: Mapping[str, Sequence[CosmosContainerRequirement]],
    create_databases_if_missing: bool = False,
) -> CosmosProvisioningResult:
    connections = _copy_cosmos_connections(cosmos_connections)
    requirements = _normalize_requirements_by_connection(
        requirements_by_connection,
        connection_names=connections,
    )
    if type(create_databases_if_missing) is not bool:
        raise TypeError('create_databases_if_missing must be a boolean')

    databases_created: list[str] = []
    containers_created: dict[str, tuple[str, ...]] = {}
    for connection_name, specs in requirements.items():
        with CosmosClient(settings=connections[connection_name]) as client:
            provisioner = CosmosProvisioner(client=client)
            if create_databases_if_missing and provisioner.ensure_database():
                databases_created.append(connection_name)
            containers_created[connection_name] = provisioner.ensure_containers(specs)

    return CosmosProvisioningResult(
        databases_created=tuple(databases_created),
        containers_created=containers_created,
    )


def _copy_cosmos_connections(
    cosmos_connections: Mapping[str, CosmosSettings],
) -> dict[str, CosmosSettings]:
    if not isinstance(cosmos_connections, Mapping):
        raise TypeError('cosmos_connections must be a mapping')
    copied = dict(cosmos_connections)
    if any(not isinstance(name, str) or not name for name in copied):
        raise TypeError('Cosmos connection names must be non-empty text')
    if any(not isinstance(settings, CosmosSettings) for settings in copied.values()):
        raise TypeError('Cosmos connection values must be CosmosSettings')
    return copied


def _normalize_requirements_by_connection(
    requirements_by_connection: Mapping[str, Sequence[CosmosContainerRequirement]],
    *,
    connection_names: Mapping[str, CosmosSettings],
) -> dict[str, tuple[CosmosContainerSpec, ...]]:
    if not isinstance(requirements_by_connection, Mapping):
        raise TypeError('requirements_by_connection must be a mapping')
    normalized: dict[str, tuple[CosmosContainerSpec, ...]] = {}
    for connection_name, requirements in requirements_by_connection.items():
        if not isinstance(connection_name, str) or not connection_name:
            raise TypeError('Cosmos requirement connection names must be non-empty text')
        if connection_name not in connection_names:
            raise ValueError(f"Unknown Cosmos connection '{connection_name}' in requirements")
        normalized[connection_name] = create_cosmos_container_specs(requirements)
    return normalized
