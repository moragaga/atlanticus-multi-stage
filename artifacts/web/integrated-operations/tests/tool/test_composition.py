from integrated_operations.tool import build_integrated_operations_tool


def _props(component):
    return component.to_plotly_json()['props']


def _walk(component):
    yield component
    children = _props(component).get('children')
    if children is None:
        return
    if not isinstance(children, (list, tuple)):
        children = (children,)
    for child in children:
        if hasattr(child, 'to_plotly_json'):
            yield from _walk(child)


def test_integrated_operations_artifact_mounts_real_tool_surfaces() -> None:
    tool = build_integrated_operations_tool()
    nodes = tuple(_walk(tool))

    assert any(
        _props(node).get('data-ada-integrated-operations-tool') == 'integrated_operations'
        for node in nodes
    )
    assert any(_props(node).get('data-section-key') == 'alarm_status' for node in nodes)
    assert any(
        _props(node).get('data-ada-alarm-baseline') == 'integrated-operations' for node in nodes
    )
    assert any(_props(node).get('data-ada-io-scope-key') == 'mine' for node in nodes)
    assert any(_props(node).get('data-ada-io-scope-key') == 'plant' for node in nodes)
    assert sum(_props(node).get('data-ada-component-card') == 'true' for node in nodes) == 22


def test_integrated_operations_starts_in_overview_without_empty_alarm_message() -> None:
    tool = build_integrated_operations_tool()
    nodes = tuple(_walk(tool))
    root = next(
        node
        for node in nodes
        if _props(node).get('data-ada-integrated-operations-tool') == 'integrated_operations'
    )
    strings = [
        _props(node).get('children')
        for node in nodes
        if isinstance(_props(node).get('children'), str)
    ]

    assert _props(root)['data-ada-io-presentation'] == 'overview'
    assert 'Sin alarmas activas' not in strings


def test_integrated_operations_artifact_exposes_overview_mine_plant_controls() -> None:
    tool = build_integrated_operations_tool()
    nodes = tuple(_walk(tool))
    targets = [
        _props(node).get('data-ada-io-presentation-target')
        for node in nodes
        if _props(node).get('data-ada-io-presentation-target')
    ]

    assert set(targets) == {'overview', 'mine', 'plant'}
    assert targets.count('overview') == 1
    assert targets.count('mine') == 2
    assert targets.count('plant') == 2
