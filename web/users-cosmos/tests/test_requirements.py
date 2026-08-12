from atlanticus.web.users.cosmos.requirements import USERS_COSMOS_REQUIREMENTS


def test_users_cosmos_declares_only_current_runtime_containers() -> None:
    assert tuple(
        (item.container_name, item.partition_key, item.ttl_seconds)
        for item in USERS_COSMOS_REQUIREMENTS
    ) == (
        ('users', '/partition_key', None),
        ('users_support', '/partition_key', None),
    )
