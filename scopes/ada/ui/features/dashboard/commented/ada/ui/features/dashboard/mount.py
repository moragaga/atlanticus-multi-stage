# Monta contenido, Stores de componente y controles de polling de forma automática a partir de DashboardDefinition.
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from dash import dcc, html
from dash.development.base_component import Component

from ada.ui.components.state_wrapper import ComponentCover, build_state_wrapper

from .definition import DashboardComponentDefinition, DashboardDefinition
from .ids import DashboardComponentIds, DashboardPollingIds
from .polling import dashboard_snapshot_channels
from .wiring import initial_render_status


@dataclass(frozen=True, slots=True)
# Conserva juntos los elementos de runtime para que el layout sólo inserte un host oculto.
class DashboardMount:
    dashboard_key: str
    component_content: Mapping[str, Component]
    stores: tuple[dcc.Store, ...]
    intervals: tuple[dcc.Interval, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, 'component_content', MappingProxyType(dict(self.component_content)))
        object.__setattr__(self, 'stores', tuple(self.stores))
        object.__setattr__(self, 'intervals', tuple(self.intervals))

    def runtime_host(self) -> html.Div:
        return html.Div((*self.stores, *self.intervals), style={'display': 'none'})

    def store_host(self) -> html.Div:
        return self.runtime_host()


# Si polling está habilitado se crean automáticamente un Store de revisión por canal y un único Interval.
def build_dashboard_mount(
    definition: DashboardDefinition,
    *,
    dashboard_key: str | None = None,
) -> DashboardMount:
    resolved_dashboard_key = dashboard_key or definition.manifest.tool_key
    content: dict[str, Component] = {}
    stores: list[dcc.Store] = []
    for component in definition.components:
        ids = DashboardComponentIds(resolved_dashboard_key, component.section.key)
        component_content, component_stores = _build_component_mount(
            component,
            ids=ids,
        )
        content[component.section.key] = component_content
        stores.extend(component_stores)
    intervals: tuple[dcc.Interval, ...] = ()
    if definition.polling is not None:
        polling_ids = DashboardPollingIds(resolved_dashboard_key)
        stores.extend(
            dcc.Store(
                id=polling_ids.revision(channel),
                storage_type='memory',
            )
            for channel in dashboard_snapshot_channels(definition)
        )
        intervals = (
            dcc.Interval(
                id=polling_ids.interval,
                interval=definition.polling.interval_milliseconds,
                n_intervals=0,
            ),
        )
    return DashboardMount(
        dashboard_key=resolved_dashboard_key,
        component_content=content,
        stores=tuple(stores),
        intervals=intervals,
    )


def _build_component_mount(
    component: DashboardComponentDefinition,
    *,
    ids: DashboardComponentIds,
) -> tuple[Component, tuple[dcc.Store, ...]]:
    if component.construction:
        return (
            build_state_wrapper(
                cover=ComponentCover.construction(),
                ready_name=_ready_name(component.section.key),
            ),
            (),
        )

    stores = _build_component_stores(component, ids=ids)
    wrapper = build_state_wrapper(
        content=[
            html.Div(id=ids.content),
            html.Div(id=ids.overlay),
        ],
        component_id=ids.wrapper,
        ready_name=_ready_name(component.section.key),
    )
    return wrapper, stores


def _build_component_stores(
    component: DashboardComponentDefinition,
    *,
    ids: DashboardComponentIds,
) -> tuple[dcc.Store, ...]:
    projection = component.projection
    if projection is None:
        return ()
    stores: list[dcc.Store] = []
    if projection.data:
        stores.append(dcc.Store(id=ids.data_store, storage_type='memory'))
    if projection.time_series:
        stores.append(dcc.Store(id=ids.time_series_store, storage_type='memory'))
    stores.extend(
        [
            dcc.Store(id=ids.state_store, storage_type='memory'),
            dcc.Store(
                id=ids.render_status_store,
                storage_type='memory',
                data=initial_render_status(component.section.key),
            ),
        ]
    )
    return tuple(stores)


def _ready_name(component_key: str) -> str:
    return component_key.replace('_', '-')
