from atlanticus.web.users.cosmos import CosmosProfileCatalog, UsersCosmosProfileCache


class EmptyUsersCosmosGateway:
    def read_state(self):
        return None

    def read_profile_catalog(self):
        raise AssertionError('Empty users projection must not read a profile catalog')


def test_empty_users_projection_uses_system_profile_catalog() -> None:
    cache = UsersCosmosProfileCache(EmptyUsersCosmosGateway())
    profiles = CosmosProfileCatalog(cache)

    assert cache.ensure_current() is None
    assert profiles.require('local').key == 'local'
    assert profiles.require('administrator').key == 'administrator'
    assert profiles.require('guest').key == 'guest'
