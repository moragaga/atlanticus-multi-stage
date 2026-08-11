# Espejo comentado: composición ADA de Identity, Users y Navigation.
from __future__ import annotations

from pathlib import Path

from ada.ui.core import create_ada_ui_module
from ada.ui.navigation import create_ada_navigation_module
from ada_ui_reference.layout import build_layout
from ada_ui_reference.module import create_reference_module
from ada_ui_reference.navigation import build_reference_navigation
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


def build_definition() -> WebApplicationDefinition:
    profiles = ProfileCatalog()
    users_runtime = UsersRuntime()
    users_resolver = UsersAccessResolver(
        source=create_local_users_source(),
        runtime=users_runtime,
        profiles=profiles,
    )
    return WebApplicationDefinition(
        import_name='ada_ui_reference',
        metadata=ApplicationMetadata(
            application_id='ada-ui-reference',
            display_name='ADA UI',
            version='0.1.0',
        ),
        publications_root=Path.cwd() / '.runtime' / 'assets',
        layout=build_layout,
        modules=(
            create_users_module(users_runtime, profiles),
            create_identity_module(
                create_local_identity_provider(),
                access_resolver=users_resolver,
            ),
            create_navigation_module(build_reference_navigation(), profiles=profiles),
            create_ada_ui_module(),
            create_ada_navigation_module(),
            create_reference_module(),
        ),
        index=IndexPageDefinition(language='es'),
    )


def create_app():
    return create_web_application(build_definition())
