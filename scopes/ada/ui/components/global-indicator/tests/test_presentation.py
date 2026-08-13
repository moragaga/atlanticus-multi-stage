from ada.ui.components.global_indicator import (
    GlobalIndicatorCollection,
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


def test_degraded_values_render_approved_status_images_without_removing_indicator() -> None:
    state = GlobalIndicatorState(
        key='recuperacion_cu',
        label='Recuperación Cu',
        unit='%',
        measurements=(
            GlobalIndicatorMeasurementState.temporal(
                DisplayValue.invalid(),
                temporality='Día',
                plan_value=DisplayValue.not_mapped(),
            ),
            GlobalIndicatorMeasurementState.temporal(
                DisplayValue.empty(),
                temporality='Semana',
                plan_value=DisplayValue.error(),
            ),
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


def test_collection_keeps_all_configured_indicators_even_when_all_values_are_degraded() -> None:
    indicators = tuple(
        GlobalIndicatorState(
            key=f'kpi_{index}',
            label=f'KPI {index}',
            unit='%',
            measurements=(
                GlobalIndicatorMeasurementState.temporal(
                    DisplayValue.invalid(),
                    temporality='Día',
                ),
            ),
        )
        for index in range(1, 9)
    )
    component = build_global_indicators(
        collection=GlobalIndicatorCollection(indicators=indicators),
    )

    assert len(component.children) == 8
