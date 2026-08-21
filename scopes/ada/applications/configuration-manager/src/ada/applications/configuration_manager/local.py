from __future__ import annotations

import os
from pathlib import Path

from ada.compositions.configuration_manager import ConfigurationManagerDependencies
from ada.configuration.tools import compose_tool_configuration_services
from ada.configuration.tools.adapters.file import (
    FileToolConfigurationSettings,
    FileToolConfigurationStore,
    FileToolProjectionRepository,
    FileToolProjectionSettings,
)
from atlanticus.web.manager import ManagerPrincipal
from atlanticus.web.navigation.configuration import compose_navigation_configuration_services
from atlanticus.web.navigation.configuration.adapters.file import (
    FileNavigationConfigurationSettings,
    FileNavigationConfigurationStore,
    FileNavigationProjectionRepository,
    FileNavigationProjectionSettings,
)
from atlanticus.web.users.configuration import (
    DiscoveredUser,
    build_user_key,
    compose_users_configuration_services,
)
from atlanticus.web.users.configuration.adapters.file import (
    FileUsersConfigurationSettings,
    FileUsersConfigurationStore,
    FileUsersProjectionRepository,
)
from atlanticus.web.users.configuration.adapters.memory import MemoryDiscoveredUsersSource


def build_local_dependencies(
    *,
    runtime_root: str | Path | None = None,
) -> ConfigurationManagerDependencies:
    resolved_root = Path(runtime_root).expanduser() if runtime_root is not None else _runtime_root()
    tools_source = FileToolConfigurationStore(
        FileToolConfigurationSettings(root=resolved_root / 'source' / 'tools')
    )
    tools_projection = FileToolProjectionRepository(
        FileToolProjectionSettings(root=resolved_root / 'projection' / 'tools')
    )
    tools = compose_tool_configuration_services(
        source=tools_source,
        publisher=tools_source,
        projection=tools_projection,
        audit_actor_provider=lambda: 'Administrador local',
    )
    users_source = FileUsersConfigurationStore(
        FileUsersConfigurationSettings(root=resolved_root / 'source' / 'users')
    )
    users_projection = FileUsersProjectionRepository(
        FileUsersConfigurationSettings(root=resolved_root / 'projection' / 'users')
    )
    users_discovered = MemoryDiscoveredUsersSource(users=list(_preview_discovered_users()))
    users = compose_users_configuration_services(
        source=users_source,
        publisher=users_source,
        projection=users_projection,
        discovered=users_discovered,
        audit_actor_provider=lambda: 'Administrador local',
    )
    navigation_source = FileNavigationConfigurationStore(
        FileNavigationConfigurationSettings(root=resolved_root / 'source' / 'navigation')
    )
    navigation_projection = FileNavigationProjectionRepository(
        FileNavigationProjectionSettings(root=resolved_root / 'projection' / 'navigation')
    )
    navigation = compose_navigation_configuration_services(
        source=navigation_source,
        publisher=navigation_source,
        projection=navigation_projection,
        audit_actor_provider=lambda: 'Administrador local',
    )
    return ConfigurationManagerDependencies(
        tools=tools,
        users=users,
        navigation=navigation,
        principal_provider=_local_manager_principal,
        tools_source_name='Archivo local',
        tools_projection_name='Archivo local',
        users_source_name='Archivo local',
        users_projection_name='Archivo local',
        navigation_source_name='Archivo local',
        navigation_projection_name='Archivo local',
    )


def _local_manager_principal() -> ManagerPrincipal:
    return ManagerPrincipal(
        subject_id='local',
        display_name='Administrador local',
        profile_keys=('administrator',),
        is_local=True,
    )


def _preview_discovered_users() -> tuple[DiscoveredUser, ...]:
    identities = (
        (
            'preview:guest-one',
            'Usuario Guest de prueba',
            'guest.one@local.atlanticus',
        ),
        (
            'preview:guest-two',
            'Segundo Guest de prueba',
            'guest.two@local.atlanticus',
        ),
    )
    return tuple(
        DiscoveredUser(
            user_id=build_user_key(
                issuer='preview',
                subject_id=subject_id,
                email=email,
            ),
            issuer='preview',
            subject_id=subject_id,
            display_name=display_name,
            email=email,
        )
        for subject_id, display_name, email in identities
    )


def _runtime_root() -> Path:
    configured = os.environ.get('CONFIGURATION_RUNTIME_PATH')
    if configured:
        return Path(configured).expanduser()
    return Path.cwd() / '.runtime' / 'configuration'
