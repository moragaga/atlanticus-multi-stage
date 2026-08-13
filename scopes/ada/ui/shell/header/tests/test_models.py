from ada.ui.components.state_wrapper import ComponentCover, CoverState
from ada.ui.shell.header import HeaderSectionStates


def test_header_section_states_can_cover_whole_global_indicator_collection() -> None:
    states = HeaderSectionStates(global_indicators=ComponentCover.stale())

    assert states.global_indicators.state is CoverState.STALE
