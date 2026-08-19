from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol


class HttpClient(Protocol):
    def request(self, method: str, endpoint: str = '', **kwargs: Any) -> Any: ...

    def request_json(self, method: str, endpoint: str = '', **kwargs: Any) -> Any: ...


class SharePointFileGateway(Protocol):
    def read(self, *, filename: str, relative_path: str) -> str | None: ...

    def write(self, *, filename: str, relative_path: str, content: str) -> None: ...


class SharePointGatewayError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PowerAutomateSharePointSettings:
    read_endpoint: str = field(default='', repr=False)
    write_endpoint: str = field(default='', repr=False)
    read_parameters: Mapping[str, str] = field(default_factory=dict, repr=False)
    write_parameters: Mapping[str, str] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            'read_endpoint',
            _normalize_optional_text(self.read_endpoint, 'read_endpoint'),
        )
        object.__setattr__(
            self,
            'write_endpoint',
            _normalize_optional_text(self.write_endpoint, 'write_endpoint'),
        )
        object.__setattr__(
            self,
            'read_parameters',
            _freeze_parameters(self.read_parameters, 'read_parameters'),
        )
        object.__setattr__(
            self,
            'write_parameters',
            _freeze_parameters(self.write_parameters, 'write_parameters'),
        )


@dataclass(frozen=True, slots=True)
class SharePointPathSettings:
    root_path: str
    tool_path: str

    def __post_init__(self) -> None:
        object.__setattr__(self, 'root_path', _normalize_relative_path(self.root_path, 'root_path'))
        object.__setattr__(self, 'tool_path', _normalize_relative_path(self.tool_path, 'tool_path'))

    @property
    def users_relative_path(self) -> str:
        return f'{self.root_path}/users'

    @property
    def navigation_relative_path(self) -> str:
        return f'{self.root_path}/{self.tool_path}/navigation'

    @property
    def tool_relative_path(self) -> str:
        return f'{self.root_path}/{self.tool_path}/tool'

    @property
    def integration_relative_path(self) -> str:
        return f'{self.root_path}/{self.tool_path}/integration'


class PowerAutomateSharePointGateway:
    def __init__(
        self,
        *,
        client: HttpClient,
        settings: PowerAutomateSharePointSettings | None = None,
    ) -> None:
        if not callable(getattr(client, 'request', None)) or not callable(
            getattr(client, 'request_json', None)
        ):
            raise TypeError('client must provide request() and request_json()')
        self._client = client
        self._settings = settings or PowerAutomateSharePointSettings()

    def read(self, *, filename: str, relative_path: str) -> str | None:
        response = self._request_read(
            {
                'filename': _require_non_empty_text(filename, 'filename'),
                'relative_path': _require_non_empty_text(relative_path, 'relative_path'),
            }
        )
        if not isinstance(response, Mapping):
            raise SharePointGatewayError('SharePoint read response must be an object')
        if response.get('success') is not True:
            raise SharePointGatewayError('SharePoint read response reported failure')
        content = response.get('content')
        if content is None:
            return None
        if not isinstance(content, str):
            raise SharePointGatewayError('SharePoint read content must be text')
        return content.strip() or None

    def write(self, *, filename: str, relative_path: str, content: str) -> None:
        if not isinstance(content, str):
            raise TypeError('content must be text')
        self._request_write(
            {
                'filename': _require_non_empty_text(filename, 'filename'),
                'relative_path': _require_non_empty_text(relative_path, 'relative_path'),
                'content': content,
            }
        )

    def _request_read(self, payload: dict[str, object]) -> object:
        try:
            return self._client.request_json(
                'POST',
                self._settings.read_endpoint,
                params=self._settings.read_parameters or None,
                json_data=payload,
            )
        except Exception as error:
            raise SharePointGatewayError('SharePoint Power Automate read failed') from error

    def _request_write(self, payload: dict[str, object]) -> None:
        try:
            self._client.request(
                'POST',
                self._settings.write_endpoint,
                params=self._settings.write_parameters or None,
                json_data=payload,
            )
        except Exception as error:
            raise SharePointGatewayError('SharePoint Power Automate write failed') from error


def _normalize_optional_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f'{field_name} must be text')
    return value.strip()


def _freeze_parameters(value: object, field_name: str) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise TypeError(f'{field_name} must be a mapping')
    normalized: dict[str, str] = {}
    for key, parameter_value in value.items():
        if not isinstance(key, str) or not key:
            raise TypeError('request parameter names must be non-empty text')
        if not isinstance(parameter_value, str):
            raise TypeError('request parameter values must be text')
        normalized[key] = parameter_value
    return MappingProxyType(normalized)


def _normalize_relative_path(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f'{field_name} must be text')
    normalized = value.strip().strip('/')
    if not normalized:
        raise ValueError(f'{field_name} must not be empty')
    if '\\' in normalized:
        raise ValueError(f'{field_name} must use forward slashes')
    segments = normalized.split('/')
    if any(not segment or segment in {'.', '..'} for segment in segments):
        raise ValueError(f'{field_name} must be a safe relative path')
    return '/'.join(segments)


def _require_non_empty_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f'{field_name} must be non-empty text')
    return value.strip()
