# Espejo pedagógico en español; la lógica ejecutable es equivalente al archivo productivo.
from __future__ import annotations

from functools import partial

from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry

from ada.runtime.web import SharedSnapshotReader

from .callbacks import register_dashboard_callbacks
from ada.features.dashboard.core.definition import DashboardDefinition
from ada.features.dashboard.core.errors import DashboardDefinitionError
from .polling import DashboardPollingErrorHandler, register_dashboard_polling_callbacks
from .wiring import ComponentRenderErrorHandler


def create_ada_dashboard_module(
    definition: DashboardDefinition,
    *,
    dashboard_key: str | None = None,
    on_error: ComponentRenderErrorHandler | None = None,
    snapshot_reader: SharedSnapshotReader | None = None,
    on_polling_error: DashboardPollingErrorHandler | None = None,
) -> WebModule:
    if definition.polling is not None and snapshot_reader is None:
        raise DashboardDefinitionError('Dashboard polling requires SharedSnapshotReader')
    return WebModule(
        name='ada-dashboard',
        register_callbacks=partial(
            _register_callbacks,
            definition=definition,
            dashboard_key=dashboard_key,
            on_error=on_error,
            snapshot_reader=snapshot_reader,
            on_polling_error=on_polling_error,
        ),
    )


def _register_callbacks(
    app,
    _services: ServiceRegistry,
    *,
    definition: DashboardDefinition,
    dashboard_key: str | None,
    on_error: ComponentRenderErrorHandler | None,
    snapshot_reader: SharedSnapshotReader | None,
    on_polling_error: DashboardPollingErrorHandler | None,
) -> None:
    register_dashboard_callbacks(
        app,
        definition,
        dashboard_key=dashboard_key,
        on_error=on_error,
    )
    if definition.polling is not None:
        if snapshot_reader is None:
            raise DashboardDefinitionError('Dashboard polling requires SharedSnapshotReader')
        register_dashboard_polling_callbacks(
            app,
            definition,
            snapshot_reader,
            dashboard_key=dashboard_key,
            on_error=on_polling_error,
        )
