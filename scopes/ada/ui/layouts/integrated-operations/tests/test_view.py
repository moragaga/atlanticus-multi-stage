from dash import html

from ada.ui.layouts.integrated_operations import (
    IntegratedOperationsLayoutError,
    IntegratedOperationsView,
    build_integrated_operations_view,
)


def _props(component):
    return component.to_plotly_json()['props']


def _view(view=IntegratedOperationsView.OVERVIEW):
    return build_integrated_operations_view(
        header_content=html.Div('header', id='header'),
        mine_alarm_pills=html.Div('mine alarms', id='mine-alarms'),
        plant_alarm_pills=html.Div('plant alarms', id='plant-alarms'),
        body_content=html.Div('body', id='body'),
        view=view,
        view_id='io-view',
    )


def test_view_owns_header_alarm_scopes_and_body_under_one_presentation_state() -> None:
    view = _view()
    props = _props(view)
    header, alarms, body, controls = props['children']
    mine_alarms, plant_alarms = _props(alarms)['children']

    assert props['id'] == 'io-view'
    assert props['data-ada-io-view-root'] == 'integrated-operations'
    assert props['data-ada-io-view'] == 'overview'
    assert _props(header)['children'].to_plotly_json()['props']['id'] == 'header'
    assert _props(body)['children'][0].to_plotly_json()['props']['id'] == 'body'
    assert _props(mine_alarms)['data-ada-io-view-scope'] == 'mine'
    assert _props(plant_alarms)['data-ada-io-view-scope'] == 'plant'
    assert _props(controls)['data-ada-io-view-controls'] == 'true'


def test_view_declares_overview_entry_close_and_direct_side_transitions() -> None:
    view = _view()
    _, _, body, controls = _props(view)['children']
    overview_controls = _props(body)['children'][1]
    overview_buttons = _props(overview_controls)['children']
    zoom_buttons = _props(controls)['children']

    assert tuple(_props(button)['data-ada-io-target-view'] for button in overview_buttons) == (
        'mine',
        'plant',
    )
    assert tuple(_props(button)['children'] for button in overview_buttons) == ('MINA', 'PLANTA')
    assert tuple(_props(button)['data-ada-io-target-view'] for button in zoom_buttons) == (
        'overview',
        'mine',
        'plant',
    )
    assert tuple(_props(button)['children'] for button in zoom_buttons) == ('×', 'MINA', 'PLANTA')


def test_view_state_changes_only_root_attribute_and_preserves_same_children() -> None:
    overview = _view(IntegratedOperationsView.OVERVIEW)
    mine = _view(IntegratedOperationsView.MINE)
    plant = _view(IntegratedOperationsView.PLANT)

    assert _props(overview)['data-ada-io-view'] == 'overview'
    assert _props(mine)['data-ada-io-view'] == 'mine'
    assert _props(plant)['data-ada-io-view'] == 'plant'
    assert (
        tuple(type(child) for child in _props(overview)['children'])
        == tuple(type(child) for child in _props(mine)['children'])
        == tuple(type(child) for child in _props(plant)['children'])
    )


def test_view_omits_optional_id_when_not_provided() -> None:
    view = build_integrated_operations_view(
        header_content=html.Div('header'),
        mine_alarm_pills=html.Div('mine'),
        plant_alarm_pills=html.Div('plant'),
        body_content=html.Div('body'),
    )

    assert 'id' not in _props(view)


def test_view_rejects_invalid_view() -> None:
    try:
        build_integrated_operations_view(
            header_content=html.Div('header'),
            mine_alarm_pills=html.Div('mine'),
            plant_alarm_pills=html.Div('plant'),
            body_content=html.Div('body'),
            view='mine',
        )
    except IntegratedOperationsLayoutError as exc:
        assert str(exc) == "Invalid integrated operations view: 'mine'"
    else:
        raise AssertionError('Expected invalid view validation error')
