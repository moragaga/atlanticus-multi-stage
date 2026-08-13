from datetime import date

from dash.development.base_component import Component

from ada.contracts.tool_manifest import ProcessBodySection, ToolScope, build_process_manifest
from ada.ui.components.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.components.global_indicator import (
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
)
from ada.ui.components.state_wrapper import ComponentCover
from ada.ui.shell.header import (
    AlarmManagementSegmentState,
    AlarmManagementState,
    HeaderIndicatorPlacement,
    HeaderSectionStates,
    build_ada_header,
    create_header_state,
)


def test_process_header_uses_generic_wrappers_and_operational_scope() -> None:
    manifest = build_process_manifest(
        tool_key='flotacion_selectiva',
        display_name='Flotación Selectiva',
        operational_scope=ToolScope.PLANT,
        body_sections=(ProcessBodySection.CENTER,),
    )
    state = create_header_state(
        manifest=manifest,
        brand=resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date(2026, 8, 12)),
        ),
        application_name='ADA',
        global_indicators=(
            HeaderIndicatorPlacement(
                section_key='global_indicators',
                scope=ToolScope.PLANT,
                indicator=GlobalIndicatorState(
                    key='recuperacion_cu',
                    label='Recuperación Cu',
                    unit='%',
                    measurements=(
                        GlobalIndicatorMeasurementState.temporal(
                            '89,4',
                            temporality='Día',
                            plan_value='90,5',
                        ),
                        GlobalIndicatorMeasurementState.last_measurement('88,9'),
                    ),
                ),
            ),
        ),
        alarm_management=AlarmManagementState(
            segments=(
                AlarmManagementSegmentState(
                    'alarm_management',
                    ToolScope.PLANT,
                    'G1',
                    50,
                ),
            )
        ),
        section_states=HeaderSectionStates(
            global_indicators=ComponentCover.stale(),
            alarm_status=ComponentCover.construction(),
        ),
    )

    component = build_ada_header(state)
    indicator = _require_by_class(component, 'ada-header__global-indicator')
    management = _require_by_class(component, 'ada-header__management-segment')
    indicators_wrapper = _require_descendant(
        _require_by_class(component, 'ada-header__indicators-slot'),
        'ada-state-wrapper',
    )
    status_wrapper = _require_descendant(
        _require_by_class(component, 'ada-header__alarm-status-slot'),
        'ada-state-wrapper',
    )

    assert _prop(indicator, 'data-scope') == 'plant'
    assert _prop(management, 'data-scope') == 'plant'
    assert _prop(indicators_wrapper, 'data-cover') == 'stale'
    assert _prop(status_wrapper, 'data-cover') == 'construction'


def _require_by_class(component: Component, class_name: str) -> Component:
    result = _find_by_class(component, class_name)
    if result is None:
        raise AssertionError(f'Component with class {class_name!r} was not found')
    return result


def _require_descendant(component: Component, class_name: str) -> Component:
    children = getattr(component, 'children', None)
    if children is None:
        raise AssertionError(f'Descendant with class {class_name!r} was not found')
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if not isinstance(child, Component):
            continue
        result = _find_by_class(child, class_name)
        if result is not None:
            return result
    raise AssertionError(f'Descendant with class {class_name!r} was not found')


def _find_by_class(component: Component, class_name: str) -> Component | None:
    classes = getattr(component, 'className', '') or ''
    if class_name in classes.split():
        return component
    children = getattr(component, 'children', None)
    if children is None:
        return None
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if isinstance(child, Component):
            result = _find_by_class(child, class_name)
            if result is not None:
                return result
    return None


def _prop(component: Component, name: str):
    return component.to_plotly_json()['props'][name]


def test_broken_global_indicator_is_covered_without_breaking_header(monkeypatch) -> None:
    import ada.ui.shell.header.presentation as header_presentation

    manifest = build_process_manifest(
        tool_key='chancado_stmg',
        display_name='Chancado STMG',
        operational_scope=ToolScope.MINE,
        body_sections=(ProcessBodySection.CENTER,),
    )
    state = create_header_state(
        manifest=manifest,
        brand=resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date(2026, 8, 12)),
        ),
        application_name='ADA',
        global_indicators=(
            HeaderIndicatorPlacement(
                section_key='global_indicators',
                scope=ToolScope.MINE,
                indicator=GlobalIndicatorState(
                    key='transportado',
                    label='Transportado',
                    unit='kt',
                    measurements=(
                        GlobalIndicatorMeasurementState.temporal(
                            '198',
                            temporality='Día',
                        ),
                    ),
                ),
            ),
        ),
    )

    def broken_renderer(*, state):
        raise RuntimeError(state.key)

    monkeypatch.setattr(header_presentation, 'build_global_indicator', broken_renderer)
    component = build_ada_header(state)
    indicator = _require_by_class(component, 'ada-header__global-indicator')
    wrapper = _require_descendant(indicator, 'ada-state-wrapper')

    assert _prop(wrapper, 'data-cover') == 'component-error'
    assert _prop(wrapper, 'data-ready') == 'true'
