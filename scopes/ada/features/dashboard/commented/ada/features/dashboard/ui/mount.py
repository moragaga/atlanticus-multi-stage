# Espejo comentado: misma lógica productiva; documenta la frontera visual de Dashboard.
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from dash import dcc, html
from dash.development.base_component import Component

from ada.features.dashboard.core.definition import (
    DashboardComponentDefinition,
    DashboardDefinition,
)
from ada.features.dashboard.core.errors import DashboardDefinitionError
from ada.ui.components.state_wrapper import ComponentCover, build_state_overlay

from .ids import DashboardComponentIds, DashboardPollingIds, DashboardSubcomponentIds
from .polling import dashboard_snapshot_channels
from .wiring import initial_render_status


# Un slot representa la única frontera donde Dashboard puede inyectar contenido/estado de una card.
@dataclass(frozen=True, slots=True)
class DashboardSubcomponentSlot:
    component_key: str
    subcomponent_key: str
    content: Component
    overlay: Component


@dataclass(frozen=True, slots=True)
class DashboardMount:
    dashboard_key: str
    subcomponent_slots: Mapping[tuple[str, str], DashboardSubcomponentSlot]
    stores: tuple[dcc.Store, ...]
    intervals: tuple[dcc.Interval, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            'subcomponent_slots',
            MappingProxyType(dict(self.subcomponent_slots)),
        )
        object.__setattr__(self, 'stores', tuple(self.stores))
        object.__setattr__(self, 'intervals', tuple(self.intervals))

    def slot(self, component_key: str, subcomponent_key: str) -> DashboardSubcomponentSlot:
        try:
            return self.subcomponent_slots[(component_key, subcomponent_key)]
        except KeyError as error:
            raise DashboardDefinitionError(
                f'Unknown dashboard subcomponent slot: {component_key!r}/{subcomponent_key!r}'
            ) from error

    def runtime_host(self) -> html.Div:
        return html.Div((*self.stores, *self.intervals), style={'display': 'none'})

    def store_host(self) -> html.Div:
        return self.runtime_host()


# El mount materializa slots, stores e intervalos una sola vez desde la definición declarativa.
def build_dashboard_mount(
    definition: DashboardDefinition,
    *,
    dashboard_key: str | None = None,
) -> DashboardMount:
    resolved_dashboard_key = dashboard_key or definition.manifest.tool_key
    slots: dict[tuple[str, str], DashboardSubcomponentSlot] = {}
    stores: list[dcc.Store] = []
    for component in definition.components:
        for section in component.subcomponents:
            if section.subcomponent is None:
                continue
            ids = DashboardSubcomponentIds(
                resolved_dashboard_key,
                component.section.key,
                section.key,
            )
            overlay = (
                build_state_overlay(ComponentCover.construction())
                if component.construction
                else None
            )
            slots[(component.section.key, section.subcomponent)] = DashboardSubcomponentSlot(
                component_key=component.section.key,
                subcomponent_key=section.subcomponent,
                # La clase confina cualquier renderer sin conocer Plotly ni la composición exterior.
                content=html.Div(id=ids.content, className='ada-dashboard-content-slot'),
                overlay=html.Div(overlay, id=ids.overlay),
            )
        if component.callback_required:
            stores.extend(
                _build_component_stores(
                    component,
                    ids=DashboardComponentIds(
                        resolved_dashboard_key,
                        component.section.key,
                    ),
                )
            )
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
        subcomponent_slots=slots,
        stores=tuple(stores),
        intervals=intervals,
    )


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
                data=initial_render_status(component),
            ),
        ]
    )
    return tuple(stores)
