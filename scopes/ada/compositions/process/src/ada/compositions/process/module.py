from __future__ import annotations

from ada.features.alarms import create_ada_alarms_module
from ada.features.dashboard import create_ada_dashboard_module
from ada.runtime.web import SharedSnapshotReader
from ada.ui.components.component_card import create_ada_component_card_module
from ada.ui.components.component_container import create_ada_component_container_module
from ada.ui.components.global_indicator import create_ada_global_indicator_module
from ada.ui.components.state_wrapper import create_ada_state_wrapper_module
from ada.ui.framework.core import create_ada_ui_module
from ada.ui.layouts.process import create_ada_process_layout_module
from ada.ui.shell.header import create_ada_header_module
from ada.ui.shell.time_status import create_ada_time_status_module
from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

from .composition import ProcessToolComposition

ADA_PROCESS_COMPOSITION_ASSET_LAYER = AssetLayer(
    name='ada_composition_process',
    load_order=280,
    package='ada.compositions.process',
)


def create_process_composition_module() -> WebModule:
    return WebModule(
        name='ada-process-composition',
        asset_layers=(ADA_PROCESS_COMPOSITION_ASSET_LAYER,),
    )


def create_process_tool_modules(
    composition: ProcessToolComposition,
    *,
    snapshot_reader: SharedSnapshotReader | None = None,
) -> tuple[WebModule, ...]:
    return (
        create_ada_ui_module(),
        create_ada_state_wrapper_module(),
        create_ada_global_indicator_module(),
        create_ada_component_container_module(),
        create_ada_component_card_module(),
        create_ada_process_layout_module(),
        create_ada_alarms_module(),
        create_ada_header_module(),
        create_ada_time_status_module(),
        create_ada_dashboard_module(
            composition.dashboard,
            dashboard_key=composition.mount.dashboard_key,
            snapshot_reader=snapshot_reader,
        ),
        create_process_composition_module(),
    )
