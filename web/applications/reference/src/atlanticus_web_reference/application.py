from __future__ import annotations

from pathlib import Path

from atlanticus.web.application import create_web_application
from atlanticus.web.compositions.users_navigation import (
    create_users_navigation_module,
    validate_users_navigation_profiles,
)
from atlanticus.web.identity.module import create_identity_module
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.models import ApplicationMetadata, WebApplicationDefinition
from atlanticus.web.navigation.api import create_navigation_module
from atlanticus.web.users.local import create_local_users_source
from atlanticus.web.users.module import create_users_module
from atlanticus.web.users.profiles import ProfileCatalog
from atlanticus.web.users.resolver import UsersAccessResolver
from atlanticus.web.users.runtime import UsersRuntime
from atlanticus_web_reference.identity import build_reference_identity_provider
from atlanticus_web_reference.layout import build_layout
from atlanticus_web_reference.modules import create_reference_module
from atlanticus_web_reference.navigation import build_reference_navigation


def build_definition() -> WebApplicationDefinition:
    profiles = ProfileCatalog()
    users_runtime = UsersRuntime()
    users_resolver = UsersAccessResolver(
        source=create_local_users_source(),
        runtime=users_runtime,
        profiles=profiles,
    )
    navigation = build_reference_navigation()
    validate_users_navigation_profiles(navigation, profiles)
    return WebApplicationDefinition(
        import_name='atlanticus_web_reference',
        metadata=ApplicationMetadata(
            application_id='atlanticus-web-reference',
            display_name='Atlanticus Web',
            version='0.1.0',
        ),
        publications_root=Path.cwd() / '.runtime' / 'assets',
        layout=build_layout,
        modules=(
            create_users_module(users_runtime, profiles),
            create_identity_module(
                build_reference_identity_provider(),
                access_resolver=users_resolver,
            ),
            create_navigation_module(navigation),
            create_users_navigation_module(),
            create_reference_module(),
        ),
        index=IndexPageDefinition(
            language='es',
            runtime_config={
                'reference': True,
            },
        ),
    )


def create_app():
    return create_web_application(build_definition())
