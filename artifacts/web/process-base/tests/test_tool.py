from process_base.tool import build_process_base_tool


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


def test_process_base_is_complete_before_real_business_renderers_are_moved_in() -> None:
    tool = build_process_base_tool()
    nodes = tuple(_walk(tool))

    assert any(_props(node).get('data-ada-process-tool') == 'process_base' for node in nodes)
    assert any(_props(node).get('data-section-key') == 'alarm_status' for node in nodes)
    assert any(_props(node).get('data-ada-process-alarm-surface') == 'true' for node in nodes)
    assert any(_props(node).get('data-ada-alarm-baseline') == 'process' for node in nodes)
    assert any(_props(node).get('data-ada-slot-key') == 'center' for node in nodes)
    assert any(_props(node).get('id') == 'process-base-layout' for node in nodes)
    assert sum(_props(node).get('data-ada-component-card') == 'true' for node in nodes) == 8


def test_dashboard_callback_targets_are_confined_inside_cards() -> None:
    tool = build_process_base_tool()
    slots = [
        node
        for node in _walk(tool)
        if _props(node).get('className') == 'ada-dashboard-content-slot'
    ]

    assert len(slots) == 8
    assert all(_props(slot).get('id', '').endswith('--content') for slot in slots)


def test_process_base_does_not_render_empty_alarm_message_when_no_active_alarms() -> None:
    tool = build_process_base_tool()
    string_children = [
        _props(node).get('children')
        for node in _walk(tool)
        if isinstance(_props(node).get('children'), str)
    ]

    assert 'Sin alarmas activas' not in string_children
