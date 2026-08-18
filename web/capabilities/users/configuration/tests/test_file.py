from pathlib import Path

from atlanticus.web.users.configuration import UsersConfigurationBundle, UsersConfigurationCatalog
from atlanticus.web.users.configuration.adapters import (
    FileUsersConfigurationSettings,
    FileUsersConfigurationStore,
    FileUsersProjectionRepository,
)


def test_file_source_and_projection_are_independent(tmp_path: Path) -> None:
    source_settings = FileUsersConfigurationSettings(root=tmp_path / 'source')
    projection_settings = FileUsersConfigurationSettings(root=tmp_path / 'projection')
    source = FileUsersConfigurationStore(source_settings)
    projection = FileUsersProjectionRepository(projection_settings)
    bundle = UsersConfigurationBundle.create(
        catalog=UsersConfigurationCatalog(
            administrator_background_color='#673AB7',
            guest_background_color='#FF5722',
        ),
        saved_by='administrator',
    )

    source.publish_bundle(bundle)

    assert source.fetch_bundle().revision == bundle.revision
    assert projection.load_state() is None

    state = projection.project(bundle, actor='administrator')

    assert projection.load_state().revision == state.revision
    assert source.fetch_bundle().revision == bundle.revision
