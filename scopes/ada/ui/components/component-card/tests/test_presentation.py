import logging

import pytest
from dash import html

from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ToolManifestLookupError,
)
from ada.ui.components.component_card import build_component_card


def _props(component):
    return component.to_plotly_json()['props']


def _flotation_card(**kwargs):
    return build_component_card(
        INTEGRATED_OPERATIONS_MANIFEST,
        component='flotacion',
        subcomponent='colectiva',
        **kwargs,
    )


def test_component_card_uses_manifest_generated_subcomponent_identity() -> None:
    card = _flotation_card(content=html.Div('Contenido'))
    props = _props(card)

    assert 'data-ada-component-key' not in props
    assert props['data-ada-component-card-component-key'] == 'flotacion'
    assert props['data-ada-subcomponent-key'] == 'flotacion_colectiva'
    assert props['data-ada-component-card'] == 'true'
    assert props['aria-label'] == 'Colectiva'


def test_component_card_preserves_injected_content() -> None:
    marker = html.Div('Injected', id='component-card-marker')
    card = _flotation_card(content=marker)
    content = _props(card)['children'][0]

    assert _props(content)['children'] is marker


def test_component_card_omits_footer_without_label_or_corner() -> None:
    card = _flotation_card(content=html.Div('Contenido'))

    assert len(_props(card)['children']) == 1


def test_component_card_supports_label_only() -> None:
    card = _flotation_card(label='Turno')
    footer = _props(card)['children'][1]
    footer_children = _props(footer)['children']

    assert len(footer_children) == 1
    assert _props(footer_children[0])['children'] == 'Turno'
    assert _props(footer_children[0])['className'] == 'ada-component-card__footer-label'


def test_component_card_supports_corner_only() -> None:
    card = _flotation_card(corner=True, corner_value='87%')
    footer = _props(card)['children'][1]
    footer_children = _props(footer)['children']

    assert len(footer_children) == 1
    assert _props(footer_children[0])['children'] == '87%'
    assert _props(footer_children[0])['data-ada-component-card-corner'] == 'true'


def test_component_card_supports_label_and_corner() -> None:
    card = _flotation_card(label='Turno', corner=True, corner_value='87%')
    footer_children = _props(_props(card)['children'][1])['children']

    assert [_props(child)['children'] for child in footer_children] == ['Turno', '87%']


def test_missing_enabled_corner_warns_and_renders_empty_value(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        card = _flotation_card(corner=True)

    corner = _props(_props(card)['children'][1])['children'][0]

    assert _props(corner)['children'] == ''
    assert 'ComponentCard corner value was not provided' in caplog.text


def test_explicit_empty_corner_does_not_warn(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        card = _flotation_card(corner=True, corner_value='')

    corner = _props(_props(card)['children'][1])['children'][0]

    assert _props(corner)['children'] == ''
    assert 'ComponentCard corner value was not provided' not in caplog.text


def test_corner_value_is_ignored_when_corner_is_disabled(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        card = _flotation_card(corner=False, corner_value='ignored')

    assert len(_props(card)['children']) == 1
    assert 'ComponentCard corner value was not provided' not in caplog.text


def test_component_card_rejects_unknown_subcomponent() -> None:
    with pytest.raises(ToolManifestLookupError, match='Unknown section key'):
        build_component_card(
            INTEGRATED_OPERATIONS_MANIFEST,
            component='flotacion',
            subcomponent='unknown',
        )
