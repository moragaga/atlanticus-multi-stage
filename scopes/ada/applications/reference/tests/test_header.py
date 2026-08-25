from ada.applications.reference.header import build_reference_header_state_from_values
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST, ToolScope


def test_reference_header_exercises_standard_two_and_three_measurement_geometry() -> None:
    state = build_reference_header_state_from_values(
        INTEGRATED_OPERATIONS_MANIFEST,
        values={},
    )
    indicators = {placement.indicator.key: placement for placement in state.global_indicators}

    assert indicators['transportado'].indicator.measurement_keys == ('turno', 'dia', 'semana')
    assert indicators['transportado'].indicator.last_measurement is not None
    assert indicators['molienda'].indicator.measurement_keys == ('dia', 'semana')
    assert indicators['molienda'].indicator.last_measurement is None
    assert indicators['cu_fino_producido'].indicator.measurement_keys == (
        'turno',
        'dia',
        'mes',
    )
    assert indicators['cu_fino_filtrado_pagable'].indicator.measurement_keys == ('dia', 'mes')


def test_reference_header_keeps_indicator_scope_explicit() -> None:
    state = build_reference_header_state_from_values(
        INTEGRATED_OPERATIONS_MANIFEST,
        values={},
    )
    scopes = {placement.indicator.key: placement.scopes for placement in state.global_indicators}

    assert scopes['transportado'] == frozenset({ToolScope.MINE})
    assert scopes['expit'] == frozenset({ToolScope.MINE})
    assert scopes['molienda'] == frozenset({ToolScope.PLANT})
    assert scopes['recuperacion_cu'] == frozenset({ToolScope.PLANT})
