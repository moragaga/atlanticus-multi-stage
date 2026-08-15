from ada.applications.reference.process import build_reference_process_layout


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


def _layout(section, layout_id: str):
    return next(item for item in _walk(section) if _props(item).get('id') == layout_id)


def _main_geometry(layout):
    main = _props(layout)['children'][0]
    return [
        (
            _props(slot)['data-ada-process-layout-role'],
            _props(slot)['className'].split()[0],
        )
        for slot in _props(main)['children']
    ]


def _cards(layout, component_key: str):
    container = next(
        item
        for item in _walk(layout)
        if _props(item).get('data-ada-component-key') == component_key
        and _props(item).get('data-ada-component-container') == 'true'
    )
    return [
        item for item in _walk(container) if _props(item).get('data-ada-component-card') == 'true'
    ]


def test_reference_process_shows_three_real_geometry_variants() -> None:
    section = build_reference_process_layout()
    center_right = _layout(section, 'reference-process-center-right')
    full = _layout(section, 'reference-process-full')
    full_bottom = _layout(section, 'reference-process-full-bottom')

    assert _main_geometry(center_right) == [('center', 'col-10'), ('right', 'col-2')]
    assert _main_geometry(full) == [
        ('left', 'col-2'),
        ('center', 'col-8'),
        ('right', 'col-2'),
    ]
    assert _main_geometry(full_bottom) == [
        ('left', 'col-2'),
        ('center', 'col-8'),
        ('right', 'col-2'),
    ]

    bottom_row = _props(full_bottom)['children'][1]
    bottom = _props(bottom_row)['children'][0]
    assert _props(bottom)['data-ada-process-layout-role'] == 'bottom'
    assert _props(bottom)['className'].split()[0] == 'col-12'


def test_reference_process_center_cardinality_is_defined_by_each_tool() -> None:
    section = build_reference_process_layout()
    center_right = _layout(section, 'reference-process-center-right')
    full = _layout(section, 'reference-process-full')
    full_bottom = _layout(section, 'reference-process-full-bottom')

    assert len(_cards(center_right, 'planta_molibdeno')) == 3
    assert len(_cards(full, 'planta_molibdeno')) == 1
    assert len(_cards(full_bottom, 'planta_molibdeno')) == 1
    assert len(_cards(full_bottom, 'graficas_tendencia')) == 1


def test_reference_process_component_names_are_exposed_once_above_cards() -> None:
    section = build_reference_process_layout()
    layout = _layout(section, 'reference-process-full')
    containers = [
        item for item in _walk(layout) if _props(item).get('data-ada-component-container') == 'true'
    ]

    assert [_props(item)['data-ada-component-key'] for item in containers] == [
        'aguas_arriba',
        'planta_molibdeno',
        'aguas_abajo',
    ]
    assert [_props(_props(item)['children'][0])['children'] for item in containers] == [
        'Aguas Arriba',
        'Planta Molibdeno',
        'Aguas Abajo',
    ]
