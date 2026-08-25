from __future__ import annotations

from dataclasses import dataclass

from dash import dcc, html

from .registry import RuntimeComponentStoreRegistry


@dataclass(frozen=True, slots=True)
class RuntimeComponentStoreMount:
    registry: RuntimeComponentStoreRegistry
    stores: tuple[dcc.Store, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'stores', tuple(self.stores))

    def runtime_host(self) -> html.Div:
        return html.Div(self.stores, style={'display': 'none'})


def build_runtime_component_store_mount(
    registry: RuntimeComponentStoreRegistry,
) -> RuntimeComponentStoreMount:
    stores: list[dcc.Store] = []
    for component in registry.components:
        stores.extend(
            (
                dcc.Store(
                    id=component.latest_store_id,
                    data=_initial_latest_data(),
                    storage_type='memory',
                ),
                dcc.Store(
                    id=component.timeseries_store_id,
                    data=_initial_timeseries_data(),
                    storage_type='memory',
                ),
            )
        )
    return RuntimeComponentStoreMount(registry=registry, stores=tuple(stores))


def _initial_latest_data() -> dict[str, object]:
    return {'state': 'unmapped', 'items': {}}


def _initial_timeseries_data() -> dict[str, object]:
    return {'state': 'unmapped', 'windows': []}
