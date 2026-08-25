# Registra assets y callbacks KPI dentro del host web Atlanticus.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
from ada.configuration.kpis.web.callbacks import register_kpi_admin_callbacks
from ada.configuration.kpis.web.models import KpiAdminWebContext
from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule


def create_kpi_admin_web_module(context: KpiAdminWebContext) -> WebModule:
    def register_callbacks(app: object, _services: object) -> None:
        register_kpi_admin_callbacks(app, context)

    return WebModule(
        name='ada-kpi-configuration',
        asset_layers=(
            AssetLayer(
                name='ada_kpi_configuration',
                load_order=720,
                package='ada.configuration.kpis',
            ),
        ),
        register_callbacks=register_callbacks,
    )
