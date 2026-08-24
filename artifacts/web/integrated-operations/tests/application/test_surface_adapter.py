from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from atlanticus.web.services import ServiceRegistry
from integrated_operations.surface import IntegratedOperationsSurfaceAdapter


def _walk(component):
    yield component
    props = component.to_plotly_json()['props']
    children = props.get('children')
    if children is None:
        return
    if not isinstance(children, (list, tuple)):
        children = (children,)
    for child in children:
        if hasattr(child, 'to_plotly_json'):
            yield from _walk(child)


def test_integrated_operations_adapter_owns_its_internal_surface_behavior() -> None:
    adapter = IntegratedOperationsSurfaceAdapter()

    surface = adapter.compose(INTEGRATED_OPERATIONS_MANIFEST)
    layout = surface.build(ServiceRegistry())
    nodes = tuple(_walk(layout))

    assert adapter.key == 'integrated_operations'
    assert adapter.supports(INTEGRATED_OPERATIONS_MANIFEST) is True
    assert surface.adapter_key == 'integrated_operations'
    assert surface.manifest == INTEGRATED_OPERATIONS_MANIFEST
    assert surface.modules
    assert any(
        node.to_plotly_json()['props'].get('data-ada-integrated-operations-tool')
        == 'integrated_operations'
        for node in nodes
    )
