# Expone la superficie administrativa KPI específica de ADA.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
from ada.configuration.kpis.web.layout import build_kpi_admin_configuration
from ada.configuration.kpis.web.models import KpiAdminWebContext
from ada.configuration.kpis.web.module import create_kpi_admin_web_module
from ada.configuration.kpis.web.preview import build_kpi_history_preview

__all__ = [
    'KpiAdminWebContext',
    'build_kpi_admin_configuration',
    'build_kpi_history_preview',
    'create_kpi_admin_web_module',
]
