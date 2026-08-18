# Dependencias explícitas de la composición ADA; los nombres indican qué backend está activo.
from dataclasses import dataclass

from ada.configuration.tools import ToolConfigurationServices
from atlanticus.web.manager import ManagerPrincipal, ManagerPrincipalProvider


@dataclass(frozen=True, slots=True)
class ConfigurationManagerDependencies:
    tools: ToolConfigurationServices
    principal_provider: ManagerPrincipalProvider
    tools_source_name: str = 'Source'
    tools_projection_name: str = 'Projection'


def local_manager_principal() -> ManagerPrincipal:
    return ManagerPrincipal(
        subject_id='local',
        display_name='Administrador local',
        profile_keys=('administrator',),
        is_local=True,
    )
