# Distingue dependencias ADA de capacidades Atlanticus y sus backends visibles.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
from dataclasses import dataclass

from ada.configuration.kpis import KpiConfigurationServices
from ada.configuration.tools import ToolConfigurationServices
from atlanticus.web.manager import ManagerPrincipalProvider
from atlanticus.web.navigation.configuration import NavigationConfigurationServices
from atlanticus.web.users.configuration import UsersConfigurationServices


@dataclass(frozen=True, slots=True)
class ConfigurationManagerDependencies:
    tools: ToolConfigurationServices
    kpis: KpiConfigurationServices
    users: UsersConfigurationServices
    navigation: NavigationConfigurationServices
    principal_provider: ManagerPrincipalProvider
    tools_source_name: str = 'Source'
    tools_projection_name: str = 'Projection'
    kpis_source_name: str = 'Source'
    kpis_projection_name: str = 'Projection'
    users_source_name: str = 'Source'
    users_projection_name: str = 'Projection'
    navigation_source_name: str = 'Source'
    navigation_projection_name: str = 'Projection'
    force_publish_enabled: bool = False
