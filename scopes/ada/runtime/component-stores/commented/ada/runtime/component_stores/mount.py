from __future__ import annotations

from dataclasses import dataclass

from dash import dcc, html

from .registry import RuntimeComponentStoreRegistry


# Agrupa los stores creados para una Tool y permite montarlos como host invisible en Dash.
@dataclass(frozen=True, slots=True)
class RuntimeComponentStoreMount:
    registry: RuntimeComponentStoreRegistry
    stores: tuple[dcc.Store, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'stores', tuple(self.stores))

    def runtime_host(self) -> html.Div:
        return html.Div(self.stores, style={'display': 'none'})


# Materializa Latest y Timeseries para todos los componentes declarados por Tool Projection.
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


# El estado inicial explícito permite que una UI exista antes del primer delivery real.
def _initial_latest_data() -> dict[str, object]:
    return {'state': 'unmapped', 'items': {}}


# Timeseries mantiene un shape propio y serializable desde el bootstrap.
def _initial_timeseries_data() -> dict[str, object]:
    return {'state': 'unmapped', 'windows': []}
