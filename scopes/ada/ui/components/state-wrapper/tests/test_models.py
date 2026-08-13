import pytest

from ada.ui.components.state_wrapper import ComponentCover, CoverState
from ada.ui.components.state_wrapper.errors import StateWrapperDefinitionError


def test_cover_states_use_dom_safe_kebab_case_values() -> None:
    assert CoverState.SOURCE_ERROR.value == 'source-error'
    assert CoverState.COMPONENT_ERROR.value == 'component-error'


def test_none_cover_rejects_overlay_content() -> None:
    with pytest.raises(StateWrapperDefinitionError):
        ComponentCover(CoverState.NONE, message='unexpected')


def test_cover_factories_are_explicit() -> None:
    assert ComponentCover.none().state is CoverState.NONE
    assert ComponentCover.stale().state is CoverState.STALE
    assert ComponentCover.construction().state is CoverState.CONSTRUCTION
    assert ComponentCover.source_error().state is CoverState.SOURCE_ERROR
    assert ComponentCover.component_error().state is CoverState.COMPONENT_ERROR
