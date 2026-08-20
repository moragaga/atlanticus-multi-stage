from __future__ import annotations

from dataclasses import dataclass

from ada.compositions.web_bootstrap import (
    AdaAccessProjectionSynchronizationResult,
    AdaConfigurationFilenames,
    AdaCosmosBindings,
    AdaWebBootstrap,
)
from atlanticus.web.compositions.runtime_infrastructure import (
    CosmosConnectionEnvironmentDefinition,
    CosmosProvisioningResult,
    SharePointEnvironmentDefinition,
    WebRuntimeInfrastructure,
)


class AdaWebDeploymentError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AdaWebDeploymentDefinition:
    cosmos_connections: tuple[CosmosConnectionEnvironmentDefinition, ...]
    bindings: AdaCosmosBindings
    sharepoint: SharePointEnvironmentDefinition
    configuration_filenames: AdaConfigurationFilenames = AdaConfigurationFilenames()

    def __post_init__(self) -> None:
        connections = tuple(self.cosmos_connections)
        if not connections:
            raise AdaWebDeploymentError(
                'ADA web deployment requires at least one Cosmos connection'
            )
        if any(not isinstance(item, CosmosConnectionEnvironmentDefinition) for item in connections):
            raise TypeError('cosmos_connections must contain Cosmos connection definitions')
        if not isinstance(self.bindings, AdaCosmosBindings):
            raise TypeError('bindings must be AdaCosmosBindings')
        if not isinstance(self.sharepoint, SharePointEnvironmentDefinition):
            raise TypeError('sharepoint must be SharePointEnvironmentDefinition')
        if not isinstance(self.configuration_filenames, AdaConfigurationFilenames):
            raise TypeError('configuration_filenames must be AdaConfigurationFilenames')
        names = tuple(item.name for item in connections)
        if len(set(names)) != len(names):
            raise AdaWebDeploymentError('Cosmos connection names must be unique')
        available = set(names)
        for capability, connection_name in (
            ('users', self.bindings.users),
            ('activity', self.bindings.activity),
            ('navigation', self.bindings.navigation),
            ('tools', self.bindings.tools),
        ):
            if connection_name not in available:
                raise AdaWebDeploymentError(
                    f"ADA capability '{capability}' references unknown Cosmos connection "
                    f"'{connection_name}'"
                )
        object.__setattr__(self, 'cosmos_connections', connections)


@dataclass(frozen=True, slots=True)
class AdaWebPreparationResult:
    provisioning: CosmosProvisioningResult
    synchronization: AdaAccessProjectionSynchronizationResult


class AdaWebDeploymentRuntime:
    __slots__ = ('_closed', 'bootstrap', 'infrastructure')

    def __init__(
        self,
        *,
        infrastructure: WebRuntimeInfrastructure,
        bootstrap: AdaWebBootstrap,
    ) -> None:
        if not isinstance(infrastructure, WebRuntimeInfrastructure):
            raise TypeError('infrastructure must be WebRuntimeInfrastructure')
        if not isinstance(bootstrap, AdaWebBootstrap):
            raise TypeError('bootstrap must be AdaWebBootstrap')
        self.infrastructure = infrastructure
        self.bootstrap = bootstrap
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        if self._closed:
            return
        self.infrastructure.close()
        self._closed = True

    def __enter__(self) -> AdaWebDeploymentRuntime:
        if self._closed:
            raise AdaWebDeploymentError('ADA web deployment runtime is closed')
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        del exc_type, exc_value, traceback
        self.close()
