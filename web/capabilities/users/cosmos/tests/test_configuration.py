from atlanticus.web.users.configuration import (
    UserConfiguration,
    UserProfileConfiguration,
    UsersConfigurationBundle,
    UsersConfigurationCatalog,
)
from atlanticus.web.users.cosmos import (
    CosmosDiscoveredUsersSource,
    CosmosUsersProjectionRepository,
)


class Client:
    def __init__(self) -> None:
        self.items = {}

    def health_check(self) -> bool:
        return True

    def find_item(self, *, container_name, item_id, partition_key):
        return self.items.get((container_name, partition_key, item_id))

    def upsert_item(self, *, container_name, item):
        key = (container_name, item['partition_key'], item['id'])
        self.items[key] = dict(item)
        return dict(item)

    def query_items(self, *, container_name, query, parameters):
        values = {item['name']: item['value'] for item in parameters}
        origin = values.get('@origin')
        return [
            item
            for (container, _, _), item in self.items.items()
            if container == container_name
            and item.get('type') == values.get('@type')
            and item.get('origin') == origin
            and (origin != 'identity' or item.get('pending') is True)
        ]


def test_cosmos_projection_writes_profiles_users_lookups_and_state() -> None:
    client = Client()
    repository = CosmosUsersProjectionRepository(client=client)
    bundle = UsersConfigurationBundle.create(
        catalog=UsersConfigurationCatalog(
            administrator_background_color='#112233',
            administrator_text_color='#FFFFFF',
            guest_background_color='#445566',
            guest_text_color='#000000',
            profiles=(
                UserProfileConfiguration(
                    key='operator',
                    label='Operador',
                    background_color='#778899',
                    text_color='#101010',
                ),
            ),
            users=(
                UserConfiguration.create(
                    user_id='user:stable',
                    issuer='entra',
                    subject_id='subject-1',
                    display_name='User One',
                    email='one@example.com',
                    profile_key='operator',
                ),
            ),
        ),
        saved_by='administrator',
    )

    state = repository.project(bundle, actor='administrator')

    profiles = client.find_item(
        container_name='users_support',
        item_id='catalog',
        partition_key='profiles',
    )
    assert profiles['schema_version'] == 2
    assert profiles['administrator_background_color'] == '#112233'
    assert profiles['administrator_text_color'] == '#FFFFFF'
    assert profiles['guest_background_color'] == '#445566'
    assert profiles['guest_text_color'] == '#000000'
    assert profiles['custom_profiles'][0]['key'] == 'operator'
    assert profiles['custom_profiles'][0]['text_color'] == '#101010'
    state_document = client.find_item(
        container_name='users_support',
        item_id='users',
        partition_key='system',
    )
    assert state_document['schema_version'] == 2
    assert repository.load_state().source_revision == bundle.revision
    assert state.source_revision == bundle.revision


def test_discovered_source_reads_identity_pending_users() -> None:
    client = Client()
    client.upsert_item(
        container_name='users',
        item={
            'id': 'user',
            'partition_key': 'user:pending',
            'type': 'user',
            'user_id': 'user:pending',
            'issuer': 'entra',
            'subject_id': 'subject-2',
            'display_name': 'Pending User',
            'email': 'pending@example.com',
            'origin': 'identity',
            'pending': True,
        },
    )

    users = CosmosDiscoveredUsersSource(client=client).list_discovered()

    assert len(users) == 1
    assert users[0].user_id == 'user:pending'
    assert users[0].email == 'pending@example.com'


def test_cosmos_projection_disables_users_removed_from_source() -> None:
    client = Client()
    repository = CosmosUsersProjectionRepository(client=client)
    first_user = UserConfiguration.create(
        user_id='user:old',
        display_name='Old User',
        email='old@example.com',
        profile_key='administrator',
    )
    first = UsersConfigurationBundle.create(
        catalog=UsersConfigurationCatalog(
            administrator_background_color='#673AB7',
            guest_background_color='#FF5722',
            users=(first_user,),
        ),
        saved_by='administrator',
    )
    repository.project(first, actor='administrator')
    second = UsersConfigurationBundle.create(
        catalog=UsersConfigurationCatalog(
            administrator_background_color='#673AB7',
            guest_background_color='#FF5722',
        ),
        saved_by='administrator',
    )

    repository.project(second, actor='administrator')

    old = client.find_item(
        container_name='users',
        item_id='user',
        partition_key='user:user:old',
    )
    assert old['enabled'] is False
    assert old['source_revision'] == second.revision
