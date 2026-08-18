# Espejo pedagógico: este archivo conserva exactamente la lógica del código productivo.
# Configuración de herramientas del scope ADA. Convierte datos administrativos mínimos en contratos runtime ToolManifest sin acoplar el dominio a la UI.
# Los comentarios explican la intención arquitectónica; no agregan ramas, estado ni comportamiento.

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ada.configuration.tools.errors import ToolConfigurationValidationError
from ada.configuration.tools.identity import require_display_name, require_identity_key
from ada.contracts.tool_manifest import ProcessBodySection, ToolScope, ToolSourceKey


class ToolConfigurationKind(StrEnum):
    INTEGRATED_OPERATIONS = 'integrated_operations'
    PROCESS = 'process'


@dataclass(frozen=True, slots=True)
class ToolSourceConfiguration:
    key: ToolSourceKey
    stale_after_seconds: int

    def __post_init__(self) -> None:
        if not isinstance(self.key, ToolSourceKey):
            raise ToolConfigurationValidationError('Tool source key is invalid')
        if isinstance(self.stale_after_seconds, bool) or not isinstance(
            self.stale_after_seconds, int
        ):
            raise ToolConfigurationValidationError('Tool source freshness must be an integer')
        if self.stale_after_seconds <= 0:
            raise ToolConfigurationValidationError(
                'Tool source freshness must be greater than zero'
            )

    def to_document(self) -> dict[str, object]:
        return {
            'key': self.key.value,
            'stale_after_seconds': self.stale_after_seconds,
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ToolSourceConfiguration:
        try:
            freshness = document['stale_after_seconds']
            if isinstance(freshness, bool) or not isinstance(freshness, int):
                raise TypeError
            return cls(
                key=ToolSourceKey(str(document['key'])),
                stale_after_seconds=freshness,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ToolConfigurationValidationError('Tool source contract is invalid') from error


@dataclass(frozen=True, slots=True)
class ToolSubcomponentConfiguration:
    key: str
    display_name: str
    linked_component_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        key = require_identity_key(self.key, label='Tool subcomponent key')
        display_name = require_display_name(
            self.display_name,
            label='Tool subcomponent display name',
        )
        linked = tuple(
            require_identity_key(value, label='Tool linked component key')
            for value in self.linked_component_keys
        )
        if len(linked) != len(set(linked)):
            raise ToolConfigurationValidationError(
                'Tool subcomponent linked component keys must be unique'
            )
        object.__setattr__(self, 'key', key)
        object.__setattr__(self, 'display_name', display_name)
        object.__setattr__(self, 'linked_component_keys', linked)

    def to_document(self) -> dict[str, object]:
        return {
            'key': self.key,
            'display_name': self.display_name,
            'linked_component_keys': list(self.linked_component_keys),
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ToolSubcomponentConfiguration:
        try:
            linked = document.get('linked_component_keys', [])
            if not isinstance(linked, list):
                raise TypeError
            return cls(
                key=str(document['key']),
                display_name=str(document['display_name']),
                linked_component_keys=tuple(str(value) for value in linked),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ToolConfigurationValidationError(
                'Tool subcomponent contract is invalid'
            ) from error


@dataclass(frozen=True, slots=True)
class ToolComponentConfiguration:
    key: str
    display_name: str
    subcomponents: tuple[ToolSubcomponentConfiguration, ...] = ()
    scope: ToolScope | None = None
    layout_role: ProcessBodySection | None = None

    def __post_init__(self) -> None:
        key = require_identity_key(self.key, label='Tool component key')
        display_name = require_display_name(self.display_name, label='Tool component display name')
        subcomponents = tuple(self.subcomponents)
        subcomponent_keys = tuple(item.key for item in subcomponents)
        if len(subcomponent_keys) != len(set(subcomponent_keys)):
            raise ToolConfigurationValidationError(
                f'Tool component {key!r} contains duplicate subcomponent keys'
            )
        if self.scope is not None and not isinstance(self.scope, ToolScope):
            raise ToolConfigurationValidationError('Tool component scope is invalid')
        if self.layout_role is not None and not isinstance(self.layout_role, ProcessBodySection):
            raise ToolConfigurationValidationError('Tool component layout role is invalid')
        object.__setattr__(self, 'key', key)
        object.__setattr__(self, 'display_name', display_name)
        object.__setattr__(self, 'subcomponents', subcomponents)

    def to_document(self) -> dict[str, object]:
        return {
            'key': self.key,
            'display_name': self.display_name,
            'scope': self.scope.value if self.scope is not None else None,
            'layout_role': self.layout_role.value if self.layout_role is not None else None,
            'subcomponents': [item.to_document() for item in self.subcomponents],
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ToolComponentConfiguration:
        try:
            subcomponents = document.get('subcomponents', [])
            if not isinstance(subcomponents, list) or not all(
                isinstance(item, dict) for item in subcomponents
            ):
                raise TypeError
            scope = _optional_string(document.get('scope'))
            layout_role = _optional_string(document.get('layout_role'))
            return cls(
                key=str(document['key']),
                display_name=str(document['display_name']),
                scope=ToolScope(scope) if scope is not None else None,
                layout_role=ProcessBodySection(layout_role) if layout_role is not None else None,
                subcomponents=tuple(
                    ToolSubcomponentConfiguration.from_document(dict(item))
                    for item in subcomponents
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ToolConfigurationValidationError('Tool component contract is invalid') from error


@dataclass(frozen=True, slots=True)
class ToolConfiguration:
    tool_key: str
    display_name: str
    kind: ToolConfigurationKind
    sources: tuple[ToolSourceConfiguration, ...] = ()
    components: tuple[ToolComponentConfiguration, ...] = ()
    operational_scope: ToolScope | None = None

    def __post_init__(self) -> None:
        tool_key = require_identity_key(self.tool_key, label='Tool key')
        display_name = require_display_name(self.display_name, label='Tool display name')
        if not isinstance(self.kind, ToolConfigurationKind):
            raise ToolConfigurationValidationError('Tool kind is invalid')
        if self.operational_scope is not None and not isinstance(self.operational_scope, ToolScope):
            raise ToolConfigurationValidationError('Tool operational scope is invalid')
        sources = tuple(self.sources)
        components = tuple(self.components)
        source_keys = tuple(source.key for source in sources)
        component_keys = tuple(component.key for component in components)
        if len(source_keys) != len(set(source_keys)):
            raise ToolConfigurationValidationError('Tool source keys must be unique')
        if len(component_keys) != len(set(component_keys)):
            raise ToolConfigurationValidationError('Tool component keys must be unique')
        object.__setattr__(self, 'tool_key', tool_key)
        object.__setattr__(self, 'display_name', display_name)
        object.__setattr__(self, 'sources', sources)
        object.__setattr__(self, 'components', components)

    @property
    def application_key(self) -> str:
        return self.kind.value

    def to_document(self) -> dict[str, object]:
        return {
            'tool_key': self.tool_key,
            'display_name': self.display_name,
            'kind': self.kind.value,
            'application_key': self.application_key,
            'operational_scope': (
                self.operational_scope.value if self.operational_scope is not None else None
            ),
            'sources': [source.to_document() for source in self.sources],
            'components': [component.to_document() for component in self.components],
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ToolConfiguration:
        try:
            sources = document.get('sources', [])
            components = document.get('components', [])
            if not isinstance(sources, list) or not all(isinstance(item, dict) for item in sources):
                raise TypeError
            if not isinstance(components, list) or not all(
                isinstance(item, dict) for item in components
            ):
                raise TypeError
            kind = ToolConfigurationKind(str(document['kind']))
            application_key = document.get('application_key')
            if application_key is not None and str(application_key) != kind.value:
                raise ToolConfigurationValidationError(
                    'Tool application key does not match tool kind'
                )
            operational_scope = _optional_string(document.get('operational_scope'))
            return cls(
                tool_key=str(document['tool_key']),
                display_name=str(document['display_name']),
                kind=kind,
                operational_scope=(
                    ToolScope(operational_scope) if operational_scope is not None else None
                ),
                sources=tuple(
                    ToolSourceConfiguration.from_document(dict(item)) for item in sources
                ),
                components=tuple(
                    ToolComponentConfiguration.from_document(dict(item)) for item in components
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ToolConfigurationValidationError(
                'Tool configuration contract is invalid'
            ) from error


@dataclass(frozen=True, slots=True)
class ToolConfigurationCatalog:
    tools: tuple[ToolConfiguration, ...]

    def __post_init__(self) -> None:
        tools = tuple(self.tools)
        keys = tuple(tool.tool_key for tool in tools)
        if len(keys) != len(set(keys)):
            raise ToolConfigurationValidationError('Tool configuration keys must be unique')
        object.__setattr__(self, 'tools', tools)

    def require(self, tool_key: str) -> ToolConfiguration:
        normalized = tool_key.strip().casefold()
        for tool in self.tools:
            if tool.tool_key == normalized:
                return tool
        raise ToolConfigurationValidationError(f'Tool configuration does not exist: {normalized}')

    def replace(self, tool: ToolConfiguration) -> ToolConfigurationCatalog:
        replaced = False
        values: list[ToolConfiguration] = []
        for current in self.tools:
            if current.tool_key == tool.tool_key:
                values.append(tool)
                replaced = True
            else:
                values.append(current)
        if not replaced:
            values.append(tool)
        return ToolConfigurationCatalog(tuple(values))

    def remove(self, tool_key: str) -> ToolConfigurationCatalog:
        normalized = tool_key.strip().casefold()
        return ToolConfigurationCatalog(
            tuple(tool for tool in self.tools if tool.tool_key != normalized)
        )

    def to_document(self) -> dict[str, object]:
        return {
            'tools': [tool.to_document() for tool in self.tools],
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ToolConfigurationCatalog:
        tools = document.get('tools')
        if not isinstance(tools, list) or not all(isinstance(item, dict) for item in tools):
            raise ToolConfigurationValidationError('Tool catalog contract is invalid')
        return cls(tuple(ToolConfiguration.from_document(dict(item)) for item in tools))


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
