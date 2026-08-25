from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from ada.configuration.tools import ToolConfigurationProjection

from .errors import RuntimeComponentStoreError


@dataclass(frozen=True, slots=True)
class RuntimeComponentStoreSpec:
    component_key: str
    wrapper_id: str
    latest_store_id: str
    timeseries_store_id: str

    def __post_init__(self) -> None:
        values = (
            (self.component_key, 'Runtime component key'),
            (self.wrapper_id, 'Runtime component wrapper id'),
            (self.latest_store_id, 'Runtime component latest store id'),
            (self.timeseries_store_id, 'Runtime component timeseries store id'),
        )
        normalized: list[str] = []
        for value, label in values:
            if not isinstance(value, str) or not value.strip():
                raise RuntimeComponentStoreError(f'{label} cannot be empty')
            normalized.append(value.strip())
        if normalized[2] == normalized[3]:
            raise RuntimeComponentStoreError('Runtime component store ids must be different')
        object.__setattr__(self, 'component_key', normalized[0])
        object.__setattr__(self, 'wrapper_id', normalized[1])
        object.__setattr__(self, 'latest_store_id', normalized[2])
        object.__setattr__(self, 'timeseries_store_id', normalized[3])


@dataclass(frozen=True, slots=True)
class RuntimeComponentStoreRegistry:
    tool_key: str
    components: tuple[RuntimeComponentStoreSpec, ...]
    _by_key: Mapping[str, RuntimeComponentStoreSpec] | None = None

    def __post_init__(self) -> None:
        tool_key = self.tool_key.strip() if isinstance(self.tool_key, str) else ''
        if not tool_key:
            raise RuntimeComponentStoreError('Runtime store registry tool key cannot be empty')
        components = tuple(self.components)
        by_key = {component.component_key: component for component in components}
        if len(by_key) != len(components):
            raise RuntimeComponentStoreError(
                'Runtime store registry contains duplicate component keys'
            )
        store_ids = tuple(
            store_id
            for component in components
            for store_id in (component.latest_store_id, component.timeseries_store_id)
        )
        if len(store_ids) != len(set(store_ids)):
            raise RuntimeComponentStoreError('Runtime component store ids must be unique')
        object.__setattr__(self, 'tool_key', tool_key)
        object.__setattr__(self, 'components', components)
        object.__setattr__(self, '_by_key', MappingProxyType(by_key))

    def component(self, component_key: str) -> RuntimeComponentStoreSpec:
        key = component_key.strip() if isinstance(component_key, str) else ''
        if not key:
            raise RuntimeComponentStoreError('Runtime component key cannot be empty')
        by_key = self._by_key
        if by_key is None:
            raise RuntimeComponentStoreError('Runtime store registry is not initialized')
        try:
            return by_key[key]
        except KeyError as error:
            raise RuntimeComponentStoreError(f'Unknown runtime component: {key!r}') from error

    def latest(self, component_key: str) -> str:
        return self.component(component_key).latest_store_id

    def timeseries(self, component_key: str) -> str:
        return self.component(component_key).timeseries_store_id


def build_runtime_component_store_registry(
    projection: ToolConfigurationProjection,
) -> RuntimeComponentStoreRegistry:
    if not isinstance(projection, ToolConfigurationProjection):
        raise RuntimeComponentStoreError('Runtime store registry requires a tool projection')
    return RuntimeComponentStoreRegistry(
        tool_key=projection.manifest.tool_key,
        components=tuple(
            RuntimeComponentStoreSpec(
                component_key=binding.component_key,
                wrapper_id=binding.wrapper_id,
                latest_store_id=binding.kpi_latest_store_id,
                timeseries_store_id=binding.kpi_timeseries_store_id,
            )
            for binding in projection.runtime.components
        ),
    )
