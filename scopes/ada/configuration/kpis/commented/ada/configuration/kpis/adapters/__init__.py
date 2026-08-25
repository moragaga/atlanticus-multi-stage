# Agrupa adapters concretos manteniendo el Core dependiente de contratos.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
from ada.configuration.kpis.adapters.cosmos import (
    CosmosKpiProjectionRepository,
    CosmosKpiProjectionSettings,
)
from ada.configuration.kpis.adapters.file import (
    FileKpiConfigurationSettings,
    FileKpiConfigurationStore,
    FileKpiProjectionRepository,
    FileKpiProjectionSettings,
)
from ada.configuration.kpis.adapters.memory import (
    MemoryKpiConfigurationStore,
    MemoryKpiProjectionRepository,
)
from ada.configuration.kpis.adapters.sharepoint import (
    SharePointKpiConfigurationSettings,
    SharePointKpiConfigurationStore,
)
from ada.configuration.kpis.adapters.tool_projection import ToolProjectionKpiDestinationProvider

__all__ = [
    'CosmosKpiProjectionRepository',
    'CosmosKpiProjectionSettings',
    'FileKpiConfigurationSettings',
    'FileKpiConfigurationStore',
    'FileKpiProjectionRepository',
    'FileKpiProjectionSettings',
    'MemoryKpiConfigurationStore',
    'MemoryKpiProjectionRepository',
    'SharePointKpiConfigurationSettings',
    'SharePointKpiConfigurationStore',
    'ToolProjectionKpiDestinationProvider',
]
