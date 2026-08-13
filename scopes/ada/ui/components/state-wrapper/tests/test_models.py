import pytest

from ada.ui.components.state_wrapper import (
    ComponentAvailability,
    DataFreshness,
    StateWrapperDefinitionError,
    StateWrapperState,
)


def test_ready_state_has_no_overlay() -> None:
    state = StateWrapperState.ready()

    assert state.availability is ComponentAvailability.READY
    assert state.freshness is DataFreshness.FRESH
    assert state.has_overlay is False


def test_stale_state_keeps_component_ready() -> None:
    state = StateWrapperState.stale()

    assert state.availability is ComponentAvailability.READY
    assert state.freshness is DataFreshness.STALE
    assert state.overlay_kind == 'stale'
    assert state.message == 'Datos desactualizados'


def test_construction_state_is_not_stale() -> None:
    state = StateWrapperState.construction()

    assert state.availability is ComponentAvailability.CONSTRUCTION
    assert state.freshness is DataFreshness.FRESH
    assert state.overlay_kind == 'construction'
    assert state.message == 'En construcción'


def test_construction_rejects_stale_freshness() -> None:
    with pytest.raises(StateWrapperDefinitionError, match='cannot declare stale'):
        StateWrapperState(
            availability=ComponentAvailability.CONSTRUCTION,
            freshness=DataFreshness.STALE,
        )
