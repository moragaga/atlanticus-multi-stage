from collections.abc import Callable
from dataclasses import dataclass

from ada.configuration.kpis.services import KpiConfigurationServices


@dataclass(frozen=True, slots=True)
class KpiAdminWebContext:
    services: KpiConfigurationServices
    draft_store_id: object
    saved_draft_store_id: object
    draft_save_action_id: object
    workflow_refresh_signal_id: object
    editor_revision_store_id: object
    workflow_tab_id: object
    workflow_panel_id: object
    content_panel_id: object
    draft_owner_provider: Callable[[], str]
    can_manage: Callable[[], bool] = lambda: True
    source_name: str = 'Source'
    projection_name: str = 'Projection'
    tools_route: str = '/manager/tools'
