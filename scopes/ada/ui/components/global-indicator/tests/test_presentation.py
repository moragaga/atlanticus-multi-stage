from ada.ui.components.global_indicator import (
    GlobalIndicatorCollection,
    GlobalIndicatorLastMeasurementState,
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
    build_global_indicator,
    build_global_indicators,
)
from ada.ui.framework.core import DisplayValue


def _props(component):
    return component.to_plotly_json()['props']


def _walk(component):
    yield component
    children = getattr(component, 'children', None)
    if children is None:
        return
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if hasattr(child, 'to_plotly_json'):
            yield from _walk(child)


def _measurement(key, label, actual, plan):
    return GlobalIndicatorMeasurementState(
        key=key,
        label=label,
        actual_value=actual,
        plan_value=plan,
    )


def test_degraded_values_render_approved_status_images_without_removing_indicator() -> None:
    state = GlobalIndicatorState(
        key='recuperacion_cu',
        label='Recuperación Cu',
        unit='%',
        measurements=(
            _measurement('dia', 'Día', DisplayValue.invalid(), DisplayValue.not_mapped()),
            _measurement('semana', 'Semana', DisplayValue.empty(), DisplayValue.error()),
        ),
    )
    component = build_global_indicator(state=state)
    images = [item for item in _walk(component) if item.__class__.__name__ == 'Img']
    sources = [_props(item)['src'] for item in images]

    assert len(images) == 4
    assert any(source.endswith('/invalid-data.svg') for source in sources)
    assert any(source.endswith('/not-mapped.svg') for source in sources)
    assert any(source.endswith('/empty-data.svg') for source in sources)
    assert any(source.endswith('/internal-error.svg') for source in sources)


def test_two_measurements_reserve_third_slot_and_optional_last_measurement_space() -> None:
    state = GlobalIndicatorState(
        key='recuperacion_cu',
        label='Recuperación Cu',
        unit='%',
        measurements=(
            _measurement('turno', 'Turno', '89,4', '90,5'),
            _measurement('dia', 'Día', '88,9', '90,0'),
        ),
    )

    component = build_global_indicator(state=state)
    rows = [item for item in _walk(component) if item.__class__.__name__ == 'Tr']
    last_slots = [
        item
        for item in _walk(component)
        if 'global-indicator__last-measurement' in (_props(item).get('className') or '')
    ]

    assert _props(component)['data-measurement-count'] == '2'
    assert _props(component)['data-measurement-capacity'] == '3'
    assert _props(component)['data-has-last-measurement'] == 'false'
    assert len(rows) == 3
    assert _props(rows[0])['data-measurement-key'] == 'turno'
    assert _props(rows[1])['data-measurement-key'] == 'dia'
    assert 'global-indicator__row--empty' in _props(rows[2])['className']
    assert len(last_slots) == 1
    assert 'global-indicator__last-measurement--empty' in _props(last_slots[0])['className']


def test_three_measurements_and_last_measurement_use_all_standard_slots() -> None:
    state = GlobalIndicatorState(
        key='recuperacion_cu',
        label='Recuperación Cu',
        unit='%',
        measurements=(
            _measurement('turno', 'Turno', '89,4', '90,5'),
            _measurement('dia', 'Día', '88,9', '90,0'),
            _measurement('semana', 'Semana', '88,1', '89,5'),
        ),
        last_measurement=GlobalIndicatorLastMeasurementState('87,9'),
    )

    component = build_global_indicator(state=state)
    rows = [item for item in _walk(component) if item.__class__.__name__ == 'Tr']
    last = next(
        item for item in _walk(component) if _props(item).get('data-measurement-key') == 'latest'
    )

    assert _props(component)['data-measurement-count'] == '3'
    assert _props(component)['data-has-last-measurement'] == 'true'
    assert tuple(_props(row)['data-measurement-key'] for row in rows) == (
        'turno',
        'dia',
        'semana',
    )
    assert _props(last)['className'] == 'global-indicator__last-measurement'


def test_collection_keeps_all_configured_indicators_even_when_all_values_are_degraded() -> None:
    indicators = tuple(
        GlobalIndicatorState(
            key=f'kpi_{index}',
            label=f'KPI {index}',
            unit='%',
            measurements=(
                _measurement('dia', 'Día', DisplayValue.invalid(), DisplayValue.not_mapped()),
                _measurement('semana', 'Semana', DisplayValue.invalid(), DisplayValue.not_mapped()),
            ),
        )
        for index in range(1, 9)
    )
    component = build_global_indicators(
        collection=GlobalIndicatorCollection(indicators=indicators),
    )

    assert len(component.children) == 8
