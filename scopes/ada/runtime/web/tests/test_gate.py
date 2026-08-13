from ada.runtime.web import Gate


def test_gate_is_non_blocking_single_flight() -> None:
    gate = Gate()

    with gate.enter() as first:
        assert first is True
        with gate.enter() as second:
            assert second is False

    with gate.enter() as third:
        assert third is True
