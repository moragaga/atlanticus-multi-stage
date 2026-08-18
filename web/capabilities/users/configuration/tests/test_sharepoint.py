import base64

from atlanticus.web.users.configuration import UsersConfigurationBundle, UsersConfigurationCatalog
from atlanticus.web.users.configuration.adapters import (
    SharePointUsersConfigurationSettings,
    SharePointUsersConfigurationStore,
)


def test_sharepoint_uses_same_generic_read_write_operation() -> None:
    stored = {'content': None}
    calls = []

    def post_json(payload: dict[str, object]):
        calls.append(dict(payload))
        if 'content' in payload:
            stored['content'] = payload['content']
            return {'ok': True}
        return {'content': stored['content']}

    store = SharePointUsersConfigurationStore(
        post_json=post_json,
        settings=SharePointUsersConfigurationSettings(),
    )
    bundle = UsersConfigurationBundle.create(
        catalog=UsersConfigurationCatalog(
            administrator_color='#673AB7',
            guest_color='#FF5722',
        ),
        saved_by='administrator',
    )

    store.publish_bundle(bundle)
    loaded = store.fetch_bundle()

    assert loaded.revision == bundle.revision
    assert base64.b64decode(stored['content'])[:2] == b'\x1f\x8b'
    assert {call['relative_path'] for call in calls} == {'users'}
    assert {call['filename'] for call in calls} == {'users_configuration.json.gz'}
