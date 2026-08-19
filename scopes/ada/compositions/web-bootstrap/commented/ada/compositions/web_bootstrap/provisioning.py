from __future__ import annotations

from collections.abc import Mapping, Sequence

from ada.compositions.web_bootstrap.models import AdaCosmosBindings, AdaWebBootstrapError
from ada.configuration.tools import TOOL_COSMOS_REQUIREMENTS
from atlanticus.connectivity.cosmos import CosmosSettings
from atlanticus.web.compositions.runtime_infrastructure import (
    CosmosContainerRequirement,
    CosmosProvisioningResult,
    ensure_cosmos_infrastructure,
)
from atlanticus.web.navigation.configuration import NAVIGATION_COSMOS_REQUIREMENTS
from atlanticus.web.users.activity import USER_ACTIVITY_COSMOS_REQUIREMENTS
from atlanticus.web.users.cosmos import USERS_COSMOS_REQUIREMENTS


def build_ada_cosmos_requirements(
    bindings: AdaCosmosBindings,
) -> Mapping[str, tuple[CosmosContainerRequirement, ...]]:
    if not isinstance(bindings, AdaCosmosBindings):
        raise TypeError('bindings must be AdaCosmosBindings')
    # Cada capability declara su contrato; ADA únicamente decide en qué conexión vive.
    grouped: dict[str, list[CosmosContainerRequirement]] = {}
    _extend(grouped, bindings.users, USERS_COSMOS_REQUIREMENTS)
    _extend(grouped, bindings.activity, USER_ACTIVITY_COSMOS_REQUIREMENTS)
    _extend(grouped, bindings.navigation, NAVIGATION_COSMOS_REQUIREMENTS)
    _extend(grouped, bindings.tools, TOOL_COSMOS_REQUIREMENTS)
    return {name: tuple(requirements) for name, requirements in grouped.items()}


def ensure_ada_cosmos_infrastructure(
    *,
    cosmos_connections: Mapping[str, CosmosSettings],
    bindings: AdaCosmosBindings,
    create_databases_if_missing: bool = False,
) -> CosmosProvisioningResult:
    # Provisioning sigue fuera del runtime; este wrapper solo proyecta el catálogo ADA.
    return ensure_cosmos_infrastructure(
        cosmos_connections=cosmos_connections,
        requirements_by_connection=build_ada_cosmos_requirements(bindings),
        create_databases_if_missing=create_databases_if_missing,
    )


def _extend(
    grouped: dict[str, list[CosmosContainerRequirement]],
    connection_name: str,
    requirements: Sequence[CosmosContainerRequirement],
) -> None:
    current = grouped.setdefault(connection_name, [])
    by_name = {requirement.container_name: requirement for requirement in current}
    for requirement in requirements:
        existing = by_name.get(requirement.container_name)
        if existing is None:
            current.append(requirement)
            by_name[requirement.container_name] = requirement
            continue
        # Dos capabilities pueden compartir un contenedor solo si su contrato físico coincide.
        if (
            existing.partition_key != requirement.partition_key
            or existing.ttl_seconds != requirement.ttl_seconds
        ):
            raise AdaWebBootstrapError(
                f"Cosmos container '{requirement.container_name}' has conflicting requirements "
                f"for connection '{connection_name}'"
            )
