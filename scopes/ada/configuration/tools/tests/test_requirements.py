from ada.configuration.tools import TOOL_COSMOS_REQUIREMENTS


def test_tools_declares_cosmos_container_requirement() -> None:
    assert [
        (item.container_name, item.partition_key, item.ttl_seconds)
        for item in TOOL_COSMOS_REQUIREMENTS
    ] == [('configuration', '/partition_key', None)]
