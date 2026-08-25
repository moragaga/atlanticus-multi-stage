from datetime import date

from dash import html
from dash.development.base_component import Component

from ada.contracts.tool_manifest import (
    ProcessBodySection,
    ToolScope,
    ToolSection,
    ToolSectionKind,
    ToolSource,
    ToolSourceKey,
    ToolTarget,
    build_process_manifest,
)
from ada.ui.components.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.components.global_indicator import (
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
)
from ada.ui.components.state_wrapper import ComponentCover
from ada.ui.shell.header import (
    HeaderIndicatorPlacement,
    HeaderSectionStates,
    build_ada_header,
    create_header_state,
)


def _process_center_component(
    *,
    key: str,
    display_name: str,
    scope: ToolScope,
) -> ToolSection:
    return ToolSection(
        key=key,
        display_name=display_name,
        kind=ToolSectionKind.COMPONENT,
        scope=scope,
        parent_key='body',
        targets=(ToolTarget.KPI, ToolTarget.ALARM),
        layout_role=ProcessBodySection.CENTER,
    )


def _process_center_card(*, component: str, subcomponent: str, scope: ToolScope) -> ToolSection:
    return ToolSection(
        component=component,
        subcomponent=subcomponent,
        display_name=subcomponent.replace('_', ' ').title(),
        kind=ToolSectionKind.SUBCOMPONENT,
        scope=scope,
        targets=(ToolTarget.ALARM,),
    )


def test_process_header_owns_slots_but_not_alarm_presentations() -> None:
    manifest = build_process_manifest(
        tool_key='flotacion_selectiva',
        display_name='Flotación Selectiva',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=300),),
        operational_scope=ToolScope.PLANT,
        body_sections=(
            _process_center_component(
                key='planta_molibdeno',
                display_name='Planta Molibdeno',
                scope=ToolScope.PLANT,
            ),
            _process_center_card(
                component='planta_molibdeno',
                subcomponent='proceso_molibdeno',
                scope=ToolScope.PLANT,
            ),
        ),
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
                scopes=frozenset({ToolScope.PLANT}),
                indicator=GlobalIndicatorState(
                    key='recuperacion_cu',
                    label='Recuperación Cu',
                    unit='%',
                    measurements=(
                        GlobalIndicatorMeasurementState(
                            key='turno',
                            label='Turno',
                            actual_value='89,4',
                            plan_value='90,5',
                        ),
                        GlobalIndicatorMeasurementState(
                            key='dia',
                            label='Día',
                            actual_value='88,9',
                            plan_value='90,0',
                        ),
                    ),
                ),
            ),
        ),
        section_states=HeaderSectionStates(
            global_indicators=ComponentCover.stale(),
        ),
    )
    management = html.Div('management', id='test-management')
    status = html.Div('status', id='test-status')

    component = build_ada_header(
        state,
        alarm_management_slot=management,
        alarm_status_slot=status,
    )
    indicators_wrapper = _require_descendant(
        _require_by_class(component, 'ada-header__indicators-slot'),
        'ada-state-wrapper',
    )
    management_slot = _require_by_class(component, 'ada-header__management-slot')
    status_slot = _require_by_class(component, 'ada-header__alarm-status-slot')

    assert _prop(indicators_wrapper, 'data-cover') == 'stale'
    assert _find_by_id(management_slot, 'test-management') is not None
    assert _find_by_id(status_slot, 'test-status') is not None
    assert _find_by_class(component, 'ada-alarm-management-summary') is None
    assert _find_by_class(component, 'ada-alarm-notifications-status') is None


def test_broken_global_indicator_is_covered_without_breaking_header(monkeypatch) -> None:
    import ada.ui.shell.header.presentation as header_presentation

    manifest = build_process_manifest(
        tool_key='chancado_stmg',
        display_name='Chancado STMG',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=300),),
        operational_scope=ToolScope.MINE,
        body_sections=(
            _process_center_component(
                key='proceso_chancado',
                display_name='Proceso Chancado',
                scope=ToolScope.MINE,
            ),
            _process_center_card(
                component='proceso_chancado',
                subcomponent='chancado_stmg',
                scope=ToolScope.MINE,
            ),
        ),
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
                scopes=frozenset({ToolScope.MINE}),
                indicator=GlobalIndicatorState(
                    key='transportado',
                    label='Transportado',
                    unit='kt',
                    measurements=(
                        GlobalIndicatorMeasurementState(
                            key='turno',
                            label='Turno',
                            actual_value='198',
                            plan_value='220',
                        ),
                        GlobalIndicatorMeasurementState(
                            key='dia',
                            label='Día',
                            actual_value='201',
                            plan_value='220',
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


def test_header_renders_shared_indicator_with_mine_and_plant_scope_tokens() -> None:
    from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST

    state = create_header_state(
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
        brand=resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date(2026, 8, 25)),
        ),
        application_name='ADA',
        global_indicators=(
            HeaderIndicatorPlacement(
                section_key='global_indicators',
                scopes=frozenset({ToolScope.MINE, ToolScope.PLANT}),
                indicator=GlobalIndicatorState(
                    key='cumplimiento_global',
                    label='Cumplimiento Global',
                    unit='%',
                    measurements=(
                        GlobalIndicatorMeasurementState(
                            key='turno',
                            label='Turno',
                            actual_value='98',
                            plan_value='100',
                        ),
                        GlobalIndicatorMeasurementState(
                            key='dia',
                            label='Día',
                            actual_value='97',
                            plan_value='100',
                        ),
                    ),
                ),
            ),
        ),
    )

    component = build_ada_header(state)
    indicator = _require_by_class(component, 'ada-header__global-indicator')

    assert _prop(indicator, 'data-scopes') == 'mine plant'


def _require_by_class(component: Component, class_name: str) -> Component:
    result = _find_by_class(component, class_name)
    if result is None:
        raise AssertionError(f'Component with class {class_name!r} was not found')
    return result


def _require_descendant(component: Component, class_name: str) -> Component:
    result = _find_by_class(component, class_name)
    if result is None or result is component:
        raise AssertionError(f'Descendant with class {class_name!r} was not found')
    return result


def _find_by_class(component: Component, class_name: str) -> Component | None:
    classes = getattr(component, 'className', '') or ''
    if class_name in classes.split():
        return component
    for child in _children(component):
        result = _find_by_class(child, class_name)
        if result is not None:
            return result
    return None


def _find_by_id(component: Component, component_id: str) -> Component | None:
    if getattr(component, 'id', None) == component_id:
        return component
    for child in _children(component):
        result = _find_by_id(child, component_id)
        if result is not None:
            return result
    return None


def _children(component: Component) -> list[Component]:
    children = getattr(component, 'children', None)
    if children is None:
        return []
    if not isinstance(children, (list, tuple)):
        children = [children]
    return [child for child in children if isinstance(child, Component)]


def _prop(component: Component, name: str):
    return component.to_plotly_json()['props'][name]


def test_header_applies_runtime_wrapper_ids_without_requiring_all_bindings() -> None:
    manifest = build_process_manifest(
        tool_key='header_runtime_reference',
        display_name='Header Runtime Reference',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=60),),
        operational_scope=ToolScope.PLANT,
        body_sections=(
            _process_center_component(
                key='process',
                display_name='Process',
                scope=ToolScope.PLANT,
            ),
            _process_center_card(
                component='process',
                subcomponent='main',
                scope=ToolScope.PLANT,
            ),
        ),
    )
    state = create_header_state(
        manifest=manifest,
        brand=resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date(2026, 8, 25)),
        ),
        application_name='ADA',
        global_indicators=(),
    )

    component = build_ada_header(
        state,
        runtime_component_wrapper_ids={
            'global_indicators': 'ada-runtime-component-global_indicators',
            'alarm_status': 'ada-runtime-component-alarm_status',
        },
    )

    assert _prop(_require_by_class(component, 'ada-header__indicators-slot'), 'id') == (
        'ada-runtime-component-global_indicators'
    )
    assert (
        'id'
        not in _require_by_class(component, 'ada-header__management-slot').to_plotly_json()['props']
    )
    assert _prop(_require_by_class(component, 'ada-header__alarm-status-slot'), 'id') == (
        'ada-runtime-component-alarm_status'
    )
