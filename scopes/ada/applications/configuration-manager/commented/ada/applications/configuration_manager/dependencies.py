from dataclasses import dataclass

from ada.configuration.tools import ToolConfigurationServices
from atlanticus.web.manager import ManagerPrincipal, ManagerPrincipalProvider
from atlanticus.web.navigation.configuration import NavigationConfigurationServices
from atlanticus.web.users.configuration import UsersConfigurationServices


@dataclass(frozen=True, slots=True)
# Define `ConfigurationManagerDependencies` como responsabilidad aislada dentro de Atlanticus.
class ConfigurationManagerDependencies:
    tools: ToolConfigurationServices
    users: UsersConfigurationServices
    navigation: NavigationConfigurationServices
    principal_provider: ManagerPrincipalProvider
    tools_source_name: str = 'Source'
    tools_projection_name: str = 'Projection'
    users_source_name: str = 'Source'
    users_projection_name: str = 'Projection'
    navigation_source_name: str = 'Source'
    navigation_projection_name: str = 'Projection'


# Resuelve `local manager principal` manteniendo validación y estado explícitos.
def local_manager_principal() -> ManagerPrincipal:
    return ManagerPrincipal(
        subject_id='local',
        display_name='Administrador local',
        profile_keys=('administrator',),
        is_local=True,
    )
