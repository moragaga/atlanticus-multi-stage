# Espejo pedagógico de la implementación productiva.
# Conserva la misma estructura y comportamiento; los comentarios documentan su responsabilidad.
from __future__ import annotations

from functools import partial
from pathlib import Path

from ada.applications.reference.configuration import resolve_reference_tool_manifest
from ada.applications.reference.layout import build_layout
from ada.applications.reference.module import create_reference_module
from ada.applications.reference.navigation import build_reference_navigation
from ada.applications.reference.runtime import create_reference_runtime_module
from ada.contracts.tool_manifest import ToolManifestResolution
from ada.ui.components.component_card import create_ada_component_card_module
from ada.ui.components.component_container import create_ada_component_container_module
from ada.ui.components.global_indicator import create_ada_global_indicator_module
from ada.ui.components.state_wrapper import create_ada_state_wrapper_module
from ada.features.alarms import create_ada_alarms_module
from ada.ui.framework.core import create_ada_ui_module
from ada.ui.layouts.integrated_operations import (
    create_ada_integrated_operations_layout_module,
)
from ada.ui.layouts.process import create_ada_process_layout_module
from ada.ui.shell.header import create_ada_header_module
from ada.ui.shell.navigation import create_ada_navigation_module
from ada.ui.shell.time_status import create_ada_time_status_module
from atlanticus.web.application import create_web_application
from atlanticus.web.identity.local import create_local_identity_provider
from atlanticus.web.identity.module import create_identity_module
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.models import ApplicationMetadata, WebApplicationDefinition
from atlanticus.web.navigation import create_navigation_module
from atlanticus.web.users.local import create_local_users_source
from atlanticus.web.users.module import create_users_module
from atlanticus.web.users.profiles import ProfileCatalog
from atlanticus.web.users.resolver import UsersAccessResolver
from atlanticus.web.users.runtime import UsersRuntime


def build_definition(
    *,
    tool_manifest_resolution: ToolManifestResolution | None = None,
) -> WebApplicationDefinition:
    resolution = (
        resolve_reference_tool_manifest()
        if tool_manifest_resolution is None
        else tool_manifest_resolution
    )
    profiles = ProfileCatalog()
    users_runtime = UsersRuntime()
    users_resolver = UsersAccessResolver(
        source=create_local_users_source(),
        runtime=users_runtime,
        profiles=profiles,
    )
    modules = [
        create_users_module(users_runtime, profiles),
        create_identity_module(
            create_local_identity_provider(),
            access_resolver=users_resolver,
        ),
        create_navigation_module(build_reference_navigation(), profiles=profiles),
    ]
    if resolution.ready:
        modules.extend(
            [
                create_reference_runtime_module(resolution.require_manifest()),
                create_ada_ui_module(),
                create_ada_navigation_module(),
                create_ada_state_wrapper_module(),
                create_ada_global_indicator_module(),
                create_ada_component_container_module(),
                create_ada_component_card_module(),
                create_ada_integrated_operations_layout_module(),
                create_ada_process_layout_module(),
                create_ada_alarms_module(),
                create_ada_header_module(),
                create_ada_time_status_module(),
            ]
        )
    else:
        modules.extend(
            [
                create_ada_ui_module(),
                create_ada_state_wrapper_module(),
            ]
        )
    modules.append(create_reference_module())

    return WebApplicationDefinition(
        import_name='ada.applications.reference',
        metadata=ApplicationMetadata(
            application_id='ada-ui-reference',
            display_name='ADA UI',
            version='0.1.0',
        ),
        publications_root=Path.cwd() / '.runtime' / 'assets',
        layout=partial(build_layout, tool_manifest_resolution=resolution),
        modules=tuple(modules),
        index=IndexPageDefinition(language='es'),
    )


def create_app():
    return create_web_application(build_definition())
