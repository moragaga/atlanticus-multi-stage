# Espejo comentado: administra clientes runtime ya configurados por la solución y no crea infraestructura Cosmos.
from __future__ import annotations

from collections.abc import Mapping

from atlanticus.connectivity.cosmos import CosmosClient, CosmosSettings
from atlanticus.connectivity.http import HttpClient
from atlanticus.web.compositions.runtime_infrastructure.configuration import (
    SharePointInfrastructureSettings,
)
from atlanticus.web.compositions.sharepoint_http import (
    PowerAutomateSharePointGateway,
    SharePointPathSettings,
)


class RuntimeInfrastructureError(RuntimeError):
    pass


class WebRuntimeInfrastructure:
    def __init__(
        self,
        *,
        cosmos_connections: Mapping[str, CosmosSettings],
        sharepoint: SharePointInfrastructureSettings | None = None,
    ) -> None:
        if not isinstance(cosmos_connections, Mapping):
            raise TypeError('cosmos_connections must be a mapping')
        copied_connections = dict(cosmos_connections)
        if any(not isinstance(name, str) or not name for name in copied_connections):
            raise TypeError('Cosmos connection names must be non-empty text')
        if any(
            not isinstance(settings, CosmosSettings)
            for settings in copied_connections.values()
        ):
            raise TypeError('Cosmos connection values must be CosmosSettings')
        if sharepoint is not None and not isinstance(sharepoint, SharePointInfrastructureSettings):
            raise TypeError('sharepoint must be SharePointInfrastructureSettings or None')

        self._cosmos_clients = {
            name: CosmosClient(settings=settings) for name, settings in copied_connections.items()
        }
        self._sharepoint_settings = sharepoint
        self._http_client = HttpClient(settings=sharepoint.http) if sharepoint is not None else None
        self._sharepoint_gateway = (
            PowerAutomateSharePointGateway(client=self._http_client, settings=sharepoint.gateway)
            if self._http_client is not None and sharepoint is not None
            else None
        )
        self._opened = False
        self._closed = False

    @property
    def cosmos_connection_names(self) -> tuple[str, ...]:
        return tuple(self._cosmos_clients)

    @property
    def sharepoint_paths(self) -> SharePointPathSettings:
        if self._sharepoint_settings is None:
            raise RuntimeInfrastructureError('SharePoint infrastructure is not configured')
        return self._sharepoint_settings.paths

    def cosmos(self, connection_name: str) -> CosmosClient:
        if not isinstance(connection_name, str) or not connection_name:
            raise TypeError('connection_name must be non-empty text')
        try:
            return self._cosmos_clients[connection_name]
        except KeyError:
            raise RuntimeInfrastructureError(
                f"Unknown Cosmos connection '{connection_name}'"
            ) from None

    def sharepoint(self) -> PowerAutomateSharePointGateway:
        if self._sharepoint_gateway is None:
            raise RuntimeInfrastructureError('SharePoint infrastructure is not configured')
        return self._sharepoint_gateway

    def open(self) -> None:
        if self._closed:
            raise RuntimeInfrastructureError('Runtime infrastructure is closed')
        if self._opened:
            return
        opened: list[object] = []
        try:
            for client in self._cosmos_clients.values():
                client.open()
                opened.append(client)
            if self._http_client is not None:
                self._http_client.open()
                opened.append(self._http_client)
        except Exception as error:
            for resource in reversed(opened):
                _close_quietly(resource)
            self._closed = True
            raise RuntimeInfrastructureError('Could not open runtime infrastructure') from error
        self._opened = True

    def close(self) -> None:
        if self._closed:
            return
        errors: list[Exception] = []
        if self._http_client is not None:
            try:
                self._http_client.close()
            except Exception as error:
                errors.append(error)
        for client in reversed(tuple(self._cosmos_clients.values())):
            try:
                client.close()
            except Exception as error:
                errors.append(error)
        self._opened = False
        self._closed = True
        if errors:
            raise RuntimeInfrastructureError(
                'Could not close runtime infrastructure'
            ) from errors[0]


def _close_quietly(resource: object) -> None:
    try:
        resource.close()
    except Exception:
        return
