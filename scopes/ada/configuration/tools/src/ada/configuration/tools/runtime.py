from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ada.configuration.tools.errors import (
    ToolConfigurationProjectionError,
    ToolConfigurationValidationError,
)
from ada.configuration.tools.identity import require_identity_key
from ada.contracts.tool_manifest import ToolManifest, ToolSectionKind

_RUNTIME_BINDINGS_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class ToolRuntimeComponentBinding:
    component_key: str
    wrapper_id: str
    kpi_latest_store_id: str
    kpi_timeseries_store_id: str

    def __post_init__(self) -> None:
        key = _require_runtime_key(self.component_key, label='Tool runtime component key')
        expected = _component_runtime_ids(key)
        actual = (
            self.wrapper_id,
            self.kpi_latest_store_id,
            self.kpi_timeseries_store_id,
        )
        if actual != expected:
            raise ToolConfigurationProjectionError(
                f'Tool runtime component binding is invalid for {key!r}'
            )
        object.__setattr__(self, 'component_key', key)

    def to_document(self) -> dict[str, str]:
        return {
            'component_key': self.component_key,
            'wrapper_id': self.wrapper_id,
            'kpi_latest_store_id': self.kpi_latest_store_id,
            'kpi_timeseries_store_id': self.kpi_timeseries_store_id,
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ToolRuntimeComponentBinding:
        try:
            return cls(
                component_key=str(document['component_key']),
                wrapper_id=str(document['wrapper_id']),
                kpi_latest_store_id=str(document['kpi_latest_store_id']),
                kpi_timeseries_store_id=str(document['kpi_timeseries_store_id']),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ToolConfigurationProjectionError(
                'Tool runtime component binding contract is invalid'
            ) from error


@dataclass(frozen=True, slots=True)
class ToolRuntimeSubcomponentBinding:
    component_key: str
    subcomponent_key: str
    linked_component_keys: tuple[str, ...]
    wrapper_id: str

    def __post_init__(self) -> None:
        component = _require_runtime_key(
            self.component_key,
            label='Tool runtime component key',
        )
        subcomponent = _require_runtime_key(
            self.subcomponent_key,
            label='Tool runtime subcomponent key',
        )
        linked = tuple(
            _require_runtime_key(value, label='Tool runtime linked component key')
            for value in self.linked_component_keys
        )
        if len(linked) != len(set(linked)):
            raise ToolConfigurationProjectionError(
                'Tool runtime linked component keys must be unique'
            )
        expected_wrapper = _subcomponent_wrapper_id(component, subcomponent)
        if self.wrapper_id != expected_wrapper:
            raise ToolConfigurationProjectionError(
                f'Tool runtime subcomponent binding is invalid for {component!r}/{subcomponent!r}'
            )
        object.__setattr__(self, 'component_key', component)
        object.__setattr__(self, 'subcomponent_key', subcomponent)
        object.__setattr__(self, 'linked_component_keys', linked)

    def to_document(self) -> dict[str, object]:
        return {
            'component_key': self.component_key,
            'subcomponent_key': self.subcomponent_key,
            'linked_component_keys': list(self.linked_component_keys),
            'wrapper_id': self.wrapper_id,
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ToolRuntimeSubcomponentBinding:
        try:
            linked = document.get('linked_component_keys', [])
            if not isinstance(linked, list):
                raise TypeError
            return cls(
                component_key=str(document['component_key']),
                subcomponent_key=str(document['subcomponent_key']),
                linked_component_keys=tuple(str(value) for value in linked),
                wrapper_id=str(document['wrapper_id']),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ToolConfigurationProjectionError(
                'Tool runtime subcomponent binding contract is invalid'
            ) from error


@dataclass(frozen=True, slots=True)
class ToolRuntimeBindings:
    components: tuple[ToolRuntimeComponentBinding, ...]
    subcomponents: tuple[ToolRuntimeSubcomponentBinding, ...]

    def __post_init__(self) -> None:
        components = tuple(self.components)
        subcomponents = tuple(self.subcomponents)
        component_keys = tuple(item.component_key for item in components)
        subcomponent_keys = tuple(
            (item.component_key, item.subcomponent_key) for item in subcomponents
        )
        wrapper_ids = tuple(item.wrapper_id for item in components) + tuple(
            item.wrapper_id for item in subcomponents
        )
        if len(component_keys) != len(set(component_keys)):
            raise ToolConfigurationProjectionError(
                'Tool runtime component bindings contain duplicate component keys'
            )
        if len(subcomponent_keys) != len(set(subcomponent_keys)):
            raise ToolConfigurationProjectionError(
                'Tool runtime subcomponent bindings contain duplicate identities'
            )
        if len(wrapper_ids) != len(set(wrapper_ids)):
            raise ToolConfigurationProjectionError('Tool runtime wrapper bindings must be unique')
        object.__setattr__(self, 'components', components)
        object.__setattr__(self, 'subcomponents', subcomponents)

    def component(self, component_key: str) -> ToolRuntimeComponentBinding:
        normalized = _require_runtime_key(
            component_key,
            label='Tool runtime component key',
        )
        for binding in self.components:
            if binding.component_key == normalized:
                return binding
        raise ToolConfigurationProjectionError(
            f'Unknown tool runtime component binding: {normalized!r}'
        )

    def subcomponent(
        self,
        *,
        component_key: str,
        subcomponent_key: str,
    ) -> ToolRuntimeSubcomponentBinding:
        component = _require_runtime_key(
            component_key,
            label='Tool runtime component key',
        )
        subcomponent = _require_runtime_key(
            subcomponent_key,
            label='Tool runtime subcomponent key',
        )
        for binding in self.subcomponents:
            if binding.subcomponent_key != subcomponent:
                continue
            if component == binding.component_key or component in binding.linked_component_keys:
                return binding
        raise ToolConfigurationProjectionError(
            f'Unknown tool runtime subcomponent binding: {component!r}/{subcomponent!r}'
        )

    def to_document(self) -> dict[str, object]:
        return {
            'schema_version': _RUNTIME_BINDINGS_SCHEMA_VERSION,
            'components': [binding.to_document() for binding in self.components],
            'subcomponents': [binding.to_document() for binding in self.subcomponents],
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ToolRuntimeBindings:
        if document.get('schema_version') != _RUNTIME_BINDINGS_SCHEMA_VERSION:
            raise ToolConfigurationProjectionError(
                'Tool runtime bindings schema version is invalid'
            )
        try:
            components = document['components']
            subcomponents = document['subcomponents']
            if not isinstance(components, list) or not all(
                isinstance(item, dict) for item in components
            ):
                raise TypeError
            if not isinstance(subcomponents, list) or not all(
                isinstance(item, dict) for item in subcomponents
            ):
                raise TypeError
            return cls(
                components=tuple(
                    ToolRuntimeComponentBinding.from_document(dict(item)) for item in components
                ),
                subcomponents=tuple(
                    ToolRuntimeSubcomponentBinding.from_document(dict(item))
                    for item in subcomponents
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ToolConfigurationProjectionError(
                'Tool runtime bindings contract is invalid'
            ) from error


def build_tool_runtime_bindings(manifest: ToolManifest) -> ToolRuntimeBindings:
    if not isinstance(manifest, ToolManifest):
        raise ToolConfigurationProjectionError('Tool runtime bindings require a tool manifest')
    components: list[ToolRuntimeComponentBinding] = []
    subcomponents: list[ToolRuntimeSubcomponentBinding] = []
    for section in manifest.sections:
        if section.kind is ToolSectionKind.COMPONENT:
            components.append(build_component_runtime_binding(section.key))
            continue
        if section.kind is ToolSectionKind.SUBCOMPONENT:
            if section.component is None or section.subcomponent is None:
                raise ToolConfigurationProjectionError(
                    'Tool runtime subcomponent identity is incomplete'
                )
            subcomponents.append(
                build_subcomponent_runtime_binding(
                    component_key=section.component,
                    subcomponent_key=section.subcomponent,
                    linked_component_keys=section.linked_component_keys,
                )
            )
    return ToolRuntimeBindings(tuple(components), tuple(subcomponents))


def build_component_runtime_binding(component_key: str) -> ToolRuntimeComponentBinding:
    key = _require_runtime_key(component_key, label='Tool runtime component key')
    wrapper_id, latest_store_id, timeseries_store_id = _component_runtime_ids(key)
    return ToolRuntimeComponentBinding(
        component_key=key,
        wrapper_id=wrapper_id,
        kpi_latest_store_id=latest_store_id,
        kpi_timeseries_store_id=timeseries_store_id,
    )


def build_subcomponent_runtime_binding(
    *,
    component_key: str,
    subcomponent_key: str,
    linked_component_keys: tuple[str, ...] = (),
) -> ToolRuntimeSubcomponentBinding:
    component = _require_runtime_key(component_key, label='Tool runtime component key')
    subcomponent = _require_runtime_key(
        subcomponent_key,
        label='Tool runtime subcomponent key',
    )
    linked = tuple(
        _require_runtime_key(value, label='Tool runtime linked component key')
        for value in linked_component_keys
    )
    return ToolRuntimeSubcomponentBinding(
        component_key=component,
        subcomponent_key=subcomponent,
        linked_component_keys=linked,
        wrapper_id=_subcomponent_wrapper_id(component, subcomponent),
    )


def _component_runtime_ids(component_key: str) -> tuple[str, str, str]:
    return (
        f'ada-runtime-component-{component_key}',
        f'ada-runtime-kpi-latest-{component_key}',
        f'ada-runtime-kpi-timeseries-{component_key}',
    )


def _subcomponent_wrapper_id(component_key: str, subcomponent_key: str) -> str:
    return f'ada-runtime-subcomponent-{component_key}-{subcomponent_key}'


def _require_runtime_key(value: str, *, label: str) -> str:
    try:
        return require_identity_key(str(value), label=label)
    except ToolConfigurationValidationError as error:
        raise ToolConfigurationProjectionError(str(error)) from error
