from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from urllib.parse import parse_qsl, urlsplit

from atlanticus.connectivity.cosmos import CosmosSettings
from atlanticus.connectivity.http import HttpAuthMode, HttpSettings
from atlanticus.web.compositions.sharepoint_http import (
    PowerAutomateSharePointSettings,
    SharePointPathSettings,
)
from atlanticus.web.environment import EnvironmentReader


@dataclass(frozen=True, slots=True)
class CosmosConnectionEnvironmentDefinition:
    name: str
    endpoint_variable: str
    key_variable: str
    database_name_variable: str
    allow_insecure_http: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, 'name', _require_name(self.name, 'name'))
        object.__setattr__(
            self,
            'endpoint_variable',
            _require_variable_name(self.endpoint_variable, 'endpoint_variable'),
        )
        object.__setattr__(
            self,
            'key_variable',
            _require_variable_name(self.key_variable, 'key_variable'),
        )
        object.__setattr__(
            self,
            'database_name_variable',
            _require_variable_name(self.database_name_variable, 'database_name_variable'),
        )
        if not isinstance(self.allow_insecure_http, bool):
            raise TypeError('allow_insecure_http must be a boolean')


@dataclass(frozen=True, slots=True)
class SharePointEnvironmentDefinition:
    read_endpoint_variable: str
    write_endpoint_variable: str
    root_path_variable: str
    tool_path_variable: str
    allow_insecure_http: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            'read_endpoint_variable',
            'write_endpoint_variable',
            'root_path_variable',
            'tool_path_variable',
        ):
            object.__setattr__(
                self,
                field_name,
                _require_variable_name(getattr(self, field_name), field_name),
            )
        if not isinstance(self.allow_insecure_http, bool):
            raise TypeError('allow_insecure_http must be a boolean')


@dataclass(frozen=True, slots=True)
class SharePointInfrastructureSettings:
    http: HttpSettings
    gateway: PowerAutomateSharePointSettings
    paths: SharePointPathSettings


def resolve_cosmos_connections(
    environment: EnvironmentReader,
    definitions: Sequence[CosmosConnectionEnvironmentDefinition],
) -> Mapping[str, CosmosSettings]:
    if not isinstance(environment, EnvironmentReader):
        raise TypeError('environment must be EnvironmentReader')
    resolved: dict[str, CosmosSettings] = {}
    for definition in definitions:
        if not isinstance(definition, CosmosConnectionEnvironmentDefinition):
            raise TypeError('Cosmos connection definitions must use the expected type')
        if definition.name in resolved:
            raise ValueError(f"Duplicate Cosmos connection definition '{definition.name}'")
        resolved[definition.name] = CosmosSettings(
            endpoint=environment.require(definition.endpoint_variable),
            key=environment.require(definition.key_variable),
            database_name=environment.require(definition.database_name_variable),
            allow_insecure_http=definition.allow_insecure_http,
        )
    return MappingProxyType(resolved)


def resolve_sharepoint_infrastructure_settings(
    environment: EnvironmentReader,
    definition: SharePointEnvironmentDefinition,
) -> SharePointInfrastructureSettings:
    if not isinstance(environment, EnvironmentReader):
        raise TypeError('environment must be EnvironmentReader')
    if not isinstance(definition, SharePointEnvironmentDefinition):
        raise TypeError('definition must be SharePointEnvironmentDefinition')
    read = _parse_power_automate_endpoint(
        environment.require(definition.read_endpoint_variable),
        definition.read_endpoint_variable,
    )
    write = _parse_power_automate_endpoint(
        environment.require(definition.write_endpoint_variable),
        definition.write_endpoint_variable,
    )
    if read.base_url != write.base_url:
        raise ValueError('SharePoint Power Automate endpoints must share the same origin')
    return SharePointInfrastructureSettings(
        http=HttpSettings(
            base_url=read.base_url,
            auth_mode=HttpAuthMode.NONE,
            allow_insecure_http=definition.allow_insecure_http,
        ),
        gateway=PowerAutomateSharePointSettings(
            read_endpoint=read.endpoint,
            write_endpoint=write.endpoint,
            read_parameters=read.parameters,
            write_parameters=write.parameters,
        ),
        paths=SharePointPathSettings(
            root_path=environment.require(definition.root_path_variable),
            tool_path=environment.require(definition.tool_path_variable),
        ),
    )


@dataclass(frozen=True, slots=True)
class _ParsedEndpoint:
    base_url: str
    endpoint: str
    parameters: Mapping[str, str]


def _parse_power_automate_endpoint(value: str, variable_name: str) -> _ParsedEndpoint:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ValueError(
            f"Environment variable '{variable_name}' must contain a valid URL"
        ) from None
    scheme = parsed.scheme.lower()
    if scheme not in {'http', 'https'} or not parsed.netloc or parsed.hostname is None:
        raise ValueError(
            f"Environment variable '{variable_name}' must contain an absolute HTTP or HTTPS URL"
        )
    if port is not None and not 1 <= port <= 65535:
        raise ValueError(f"Environment variable '{variable_name}' must contain a valid port")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(f"Environment variable '{variable_name}' must not contain credentials")
    if parsed.fragment:
        raise ValueError(f"Environment variable '{variable_name}' must not contain a fragment")
    if not parsed.path or parsed.path == '/':
        raise ValueError(f"Environment variable '{variable_name}' must contain an endpoint path")

    pairs = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
    parameters = dict(pairs)
    if len(parameters) != len(pairs):
        raise ValueError(
            f"Environment variable '{variable_name}' must not contain duplicate query parameters"
        )
    authority = f'{parsed.scheme.lower()}://{parsed.netloc}/'
    return _ParsedEndpoint(
        base_url=authority,
        endpoint=parsed.path.lstrip('/'),
        parameters=MappingProxyType(parameters),
    )


def _require_name(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f'{field_name} must be non-empty text')
    normalized = value.strip()
    if normalized != value:
        raise ValueError(f'{field_name} must not contain surrounding whitespace')
    return normalized


def _require_variable_name(value: object, field_name: str) -> str:
    normalized = _require_name(value, field_name)
    if '=' in normalized or '\x00' in normalized:
        raise ValueError(f'{field_name} must contain a valid environment variable name')
    return normalized
