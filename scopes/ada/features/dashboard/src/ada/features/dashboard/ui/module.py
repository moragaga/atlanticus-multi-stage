from __future__ import annotations

from functools import partial

from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry

from ada.features.dashboard.core.definition import DashboardDefinition
from ada.features.dashboard.core.errors import DashboardDefinitionError
from ada.runtime.web import SharedSnapshotReader

from .callbacks import register_dashboard_callbacks
from .polling import DashboardPollingErrorHandler, register_dashboard_polling_callbacks
from .wiring import ComponentRenderErrorHandler

ADA_DASHBOARD_ASSET_LAYER = AssetLayer(
    name='ada_feature_dashboard',
    load_order=245,
    package='ada.features.dashboard.ui',
)


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
        asset_layers=(ADA_DASHBOARD_ASSET_LAYER,),
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
