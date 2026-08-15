from ada.applications.reference.process import build_reference_process_layout


def _props(component):
    return component.to_plotly_json()['props']


def test_reference_process_uses_functional_regions_and_full_geometry() -> None:
    section = build_reference_process_layout()
    layout = _props(section)['children'][2]
    main, bottom = _props(layout)['children']
    main_regions = _props(main)['children']
    bottom_region = _props(bottom)['children'][0]

    assert _props(layout)['id'] == 'reference-process-layout'
    assert [(_props(region)['data-ada-process-region-key']) for region in main_regions] == [
        'aguas_arriba',
        'planta_molibdeno',
        'aguas_abajo',
    ]
    assert [(_props(region)['data-ada-process-layout-role']) for region in main_regions] == [
        'left',
        'center',
        'right',
    ]
    assert [_props(region)['className'].split()[0] for region in main_regions] == [
        'col-2',
        'col-8',
        'col-2',
    ]
    assert _props(bottom_region)['data-ada-process-layout-role'] == 'bottom'
    assert _props(bottom_region)['className'].split()[0] == 'col-12'


def test_reference_process_center_and_bottom_are_single_units() -> None:
    section = build_reference_process_layout()
    layout = _props(section)['children'][2]
    main, bottom = _props(layout)['children']
    left, center, right = _props(main)['children']
    bottom_region = _props(bottom)['children'][0]

    left_content = _props(_props(left)['children'][1])['children']
    center_content = _props(_props(center)['children'][1])['children']
    right_content = _props(_props(right)['children'][1])['children']
    bottom_content = _props(_props(bottom_region)['children'][1])['children']

    assert _props(left_content)['className'] == 'd-flex flex-column gap-1'
    assert len(_props(left_content)['children']) == 2
    assert _props(right_content)['className'] == 'd-flex flex-column gap-1'
    assert len(_props(right_content)['children']) == 2
    assert _props(center_content)['className'] == 'reference-ada__process-content-card flex-fill'
    assert _props(center_content)['children'] == 'Contenido central'
    assert _props(bottom_content)['className'] == 'reference-ada__process-content-card flex-fill'
    assert _props(bottom_content)['children'] == 'Bottom opcional'
