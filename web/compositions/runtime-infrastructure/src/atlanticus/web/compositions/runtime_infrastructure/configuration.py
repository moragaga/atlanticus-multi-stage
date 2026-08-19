from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from urllib.parse import parse_qsl, urlsplit

from atlanticus.configuration import ConfigurationVariableSpec, ResolvedConfiguration
from atlanticus.connectivity.http import HttpAuthMode, HttpSettings
from atlanticus.web.compositions.sharepoint_http import (
    PowerAutomateSharePointSettings,
    SharePointPathSettings,
)

SHAREPOINT_READ_ENDPOINT_VARIABLE = 'ATLANTICUS_SHAREPOINT_READ_ENDPOINT'
SHAREPOINT_WRITE_ENDPOINT_VARIABLE = 'ATLANTICUS_SHAREPOINT_WRITE_ENDPOINT'
SHAREPOINT_ROOT_PATH_VARIABLE = 'ATLANTICUS_SHAREPOINT_ROOT_PATH'
SHAREPOINT_TOOL_PATH_VARIABLE = 'ATLANTICUS_SHAREPOINT_TOOL_PATH'


@dataclass(frozen=True, slots=True)
class SharePointInfrastructureSettings:
    http: HttpSettings
    gateway: PowerAutomateSharePointSettings
    paths: SharePointPathSettings


def create_sharepoint_configuration_specs() -> tuple[ConfigurationVariableSpec, ...]:
    return (
        ConfigurationVariableSpec(key=SHAREPOINT_READ_ENDPOINT_VARIABLE, sensitive=True),
        ConfigurationVariableSpec(key=SHAREPOINT_WRITE_ENDPOINT_VARIABLE, sensitive=True),
        ConfigurationVariableSpec(key=SHAREPOINT_ROOT_PATH_VARIABLE),
        ConfigurationVariableSpec(key=SHAREPOINT_TOOL_PATH_VARIABLE),
    )


def resolve_sharepoint_infrastructure_settings(
    configuration: ResolvedConfiguration,
) -> SharePointInfrastructureSettings:
    _require_resolved_configuration(configuration)
    read = _parse_power_automate_endpoint(
        configuration.require(SHAREPOINT_READ_ENDPOINT_VARIABLE),
        SHAREPOINT_READ_ENDPOINT_VARIABLE,
    )
    write = _parse_power_automate_endpoint(
        configuration.require(SHAREPOINT_WRITE_ENDPOINT_VARIABLE),
        SHAREPOINT_WRITE_ENDPOINT_VARIABLE,
    )
    if read.base_url != write.base_url:
        raise ValueError('SharePoint Power Automate endpoints must share the same origin')
    return SharePointInfrastructureSettings(
        http=HttpSettings(
            base_url=read.base_url,
            auth_mode=HttpAuthMode.NONE,
            allow_insecure_http=configuration.environment.is_local,
        ),
        gateway=PowerAutomateSharePointSettings(
            read_endpoint=read.endpoint,
            write_endpoint=write.endpoint,
            read_parameters=read.parameters,
            write_parameters=write.parameters,
        ),
        paths=SharePointPathSettings(
            root_path=configuration.require(SHAREPOINT_ROOT_PATH_VARIABLE),
            tool_path=configuration.require(SHAREPOINT_TOOL_PATH_VARIABLE),
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


def _require_resolved_configuration(configuration: object) -> None:
    if not isinstance(configuration, ResolvedConfiguration):
        raise TypeError('configuration must be ResolvedConfiguration')
