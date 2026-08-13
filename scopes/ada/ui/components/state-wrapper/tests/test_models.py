import pytest

from ada.ui.components.state_wrapper import (
    ComponentCover,
    CoverState,
    StateWrapperDefinitionError,
)


def test_uncovered_component_has_no_overlay() -> None:
    cover = ComponentCover.none()

    assert cover.state is CoverState.NONE
    assert cover.covered is False


def test_transversal_cover_states_have_clear_defaults() -> None:
    assert ComponentCover.stale().state is CoverState.STALE
    assert ComponentCover.construction().state is CoverState.CONSTRUCTION
    assert ComponentCover.source_error().state is CoverState.SOURCE_ERROR
    assert ComponentCover.component_error().state is CoverState.COMPONENT_ERROR


def test_uncovered_component_rejects_overlay_content() -> None:
    with pytest.raises(StateWrapperDefinitionError, match='cannot declare overlay content'):
        ComponentCover(CoverState.NONE, message='No corresponde')
