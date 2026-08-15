import pytest
from dash import html

from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from ada.ui.components.component_container import (
    ComponentContainerDefinitionError,
    build_component_container,
)


def _props(component):
    return component.to_plotly_json()['props']


def test_component_container_exposes_component_identity_title_and_opaque_content() -> None:
    marker = html.Div('Injected', id='marker')

    container = build_component_container(
        INTEGRATED_OPERATIONS_MANIFEST,
        component='flotacion',
        content=marker,
        class_name='custom-class',
    )
    props = _props(container)
    title, content = props['children']

    assert props['data-ada-component-container'] == 'true'
    assert props['data-ada-component-key'] == 'flotacion'
    assert props['aria-label'] == 'Flotación'
    assert props['className'] == 'ada-component-container custom-class'
    assert _props(title)['children'] == 'Flotación'
    assert _props(content)['children'] is marker


def test_component_container_rejects_non_component_section() -> None:
    with pytest.raises(
        ComponentContainerDefinitionError,
        match="Section 'plant' is not a component",
    ):
        build_component_container(
            INTEGRATED_OPERATIONS_MANIFEST,
            component='plant',
            content=html.Div('Invalid'),
        )
