from dash import Dash

from ada.configuration.kpis.adapters import (
    MemoryKpiConfigurationStore,
    MemoryKpiProjectionRepository,
)
from ada.configuration.kpis.destinations import KpiDestinationCatalog
from ada.configuration.kpis.services import compose_kpi_configuration_services
from ada.configuration.kpis.web.callbacks import register_kpi_admin_callbacks
from ada.configuration.kpis.web.models import KpiAdminWebContext


class _Destinations:
    def load(self) -> KpiDestinationCatalog | None:
        return None


def _context() -> KpiAdminWebContext:
    source = MemoryKpiConfigurationStore()
    services = compose_kpi_configuration_services(
        source=source,
        publisher=source,
        projection=MemoryKpiProjectionRepository(),
        destinations=_Destinations(),
        audit_actor_provider=lambda: 'Test User',
    )
    return KpiAdminWebContext(
        services=services,
        draft_store_id='test-kpi-draft-store',
        draft_save_action_id='test-kpi-draft-save',
        workflow_refresh_signal_id='test-kpi-workflow-refresh',
        editor_revision_store_id='test-kpi-editor-revision',
        workflow_tab_id='test-kpi-workflow-tab',
        workflow_panel_id='test-kpi-workflow-panel',
        content_panel_id='test-kpi-content-panel',
        draft_owner_provider=lambda: 'test-user',
    )


def test_kpi_admin_callbacks_register_with_real_dash_application() -> None:
    app = Dash(__name__)

    register_kpi_admin_callbacks(app, _context())

    assert app.callback_map
