# Espejo pedagógico: conserva la misma lógica del archivo productivo.
# Los comentarios documentan la responsabilidad sin cambiar el comportamiento.
# Compone simuladores locales sin convertir el filesystem en draft durable.
from __future__ import annotations

import os
from pathlib import Path

from ada.applications.configuration_manager.dependencies import (
    ConfigurationManagerDependencies,
    local_manager_principal,
)
from ada.configuration.tools import compose_tool_configuration_services
from ada.configuration.tools.adapters.file import (
    FileToolConfigurationSettings,
    FileToolConfigurationStore,
    FileToolProjectionRepository,
    FileToolProjectionSettings,
)


def build_local_dependencies(
    *,
    runtime_root: str | Path | None = None,
) -> ConfigurationManagerDependencies:
    resolved_root = Path(runtime_root).expanduser() if runtime_root is not None else _runtime_root()
    source = FileToolConfigurationStore(
        FileToolConfigurationSettings(root=resolved_root / 'source' / 'tools')
    )
    projection = FileToolProjectionRepository(
        FileToolProjectionSettings(root=resolved_root / 'projection' / 'tools')
    )
    services = compose_tool_configuration_services(
        source=source,
        publisher=source,
        projection=projection,
        audit_actor_provider=lambda: 'Administrador local',
    )
    return ConfigurationManagerDependencies(
        tools=services,
        principal_provider=local_manager_principal,
        tools_source_name='Archivo local',
        tools_projection_name='Archivo local',
    )


def _runtime_root() -> Path:
    configured = os.environ.get('CONFIGURATION_RUNTIME_PATH')
    if configured:
        return Path(configured).expanduser()
    return Path.cwd() / '.runtime' / 'configuration'
