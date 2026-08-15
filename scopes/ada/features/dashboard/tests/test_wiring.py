from datetime import UTC, datetime

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
from ada.features.dashboard import (
    ComponentDataSnapshot,
    ComponentProjectionDefinition,
    ComponentProjectionState,
    ComponentRendererDefinition,
    ComponentRendererRegistry,
    ComponentRenderState,
    ComponentRenderStatus,
    ComponentStateSnapshot,
    ComponentTimeSeriesSnapshot,
    DashboardDefinition,
    DashboardToolConfiguration,
    TimeSeriesProjectionDefinition,
    TimeSeriesSettings,
    TimeSeriesWindowSnapshot,
    encode_component_data_snapshot,
    encode_component_state_snapshot,
    encode_component_time_series_snapshot,
    encode_render_status,
    initial_render_status,
    render_component_from_stores,
    resolve_subcomponent_cover,
)
from ada.ui.components.state_wrapper import CoverState


def _manifest():
    return build_process_manifest(
        tool_key='process_wiring',
        display_name='Process Wiring',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=60),),
        operational_scope=ToolScope.PLANT,
        body_sections=(
            ToolSection(
                key='center_process',
                display_name='Proceso Central',
                kind=ToolSectionKind.COMPONENT,
                scope=ToolScope.PLANT,
                parent_key='body',
                targets=(ToolTarget.KPI, ToolTarget.ALARM),
                layout_role=ProcessBodySection.CENTER,
            ),
            ToolSection(
                component='center_process',
                subcomponent='main',
                display_name='Principal',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=ToolScope.PLANT,
                targets=(ToolTarget.ALARM,),
            ),
            ToolSection(
                component='center_process',
                subcomponent='secondary',
                display_name='Secundario',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=ToolScope.PLANT,
                targets=(ToolTarget.ALARM,),
            ),
        ),
    )


def _definition(renderer):
    return DashboardDefinition.build(
        manifest=_manifest(),
        configuration=DashboardToolConfiguration(
            components=(
                ComponentProjectionDefinition(
                    component_key='center_process',
                    data=True,
                    time_series=(TimeSeriesProjectionDefinition(key='ley', hours=1),),
                ),
            ),
            time_series=TimeSeriesSettings(
                step_seconds=600,
                display_timezone='America/Santiago',
            ),
        ),
        renderers=ComponentRendererRegistry(
            definitions=(
                ComponentRendererDefinition(component_key='center_process', renderer=renderer),
            )
        ),
    )


def _data():
    return encode_component_data_snapshot(
        ComponentDataSnapshot(
            component_key='center_process',
            payload={'kpi': 87},
        )
    )


def _time_series(*, key='ley', hours=1):
    return encode_component_time_series_snapshot(
        ComponentTimeSeriesSnapshot(
            component_key='center_process',
            windows=(
                TimeSeriesWindowSnapshot(
                    hours=hours,
                    start_utc=datetime(2026, 8, 15, 11, 0, tzinfo=UTC),
                    end_utc=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
                    series={key: [1, 2, 3, 4, 5, 6]},
                ),
            ),
        )
    )


def _rendered(bundle):
    return {'main': bundle.data['kpi'], 'secondary': 'ok'}


def test_render_waits_until_all_required_projections_are_available() -> None:
    calls = []
    definition = _definition(lambda bundle: calls.append(bundle) or _rendered(bundle))

    result = render_component_from_stores(
        component=definition.component('center_process'),
        configuration=definition.configuration,
        data_value=_data(),
        time_series_value=None,
    )

    assert result.status.state('main') is ComponentRenderState.WAITING
    assert result.status.state('secondary') is ComponentRenderState.WAITING
    assert result.preserve_content is True
    assert calls == []


def test_render_returns_content_by_subcomponent_and_hydrates_time_axis() -> None:
    observed = []
    definition = _definition(lambda bundle: observed.append(bundle) or _rendered(bundle))

    result = render_component_from_stores(
        component=definition.component('center_process'),
        configuration=definition.configuration,
        data_value=_data(),
        time_series_value=_time_series(),
    )

    assert result.content == {'main': 87, 'secondary': 'ok'}
    assert result.status.state('main') is ComponentRenderState.READY
    assert len(observed[0].time_series[1].axis.utc) == 6


def test_renderer_must_return_exact_subcomponent_mapping() -> None:
    definition = _definition(lambda _bundle: {'main': 'only-one'})

    result = render_component_from_stores(
        component=definition.component('center_process'),
        configuration=definition.configuration,
        data_value=_data(),
        time_series_value=_time_series(),
    )

    assert result.preserve_content is True
    assert result.status.state('main') is ComponentRenderState.ERROR
    assert result.status.state('secondary') is ComponentRenderState.ERROR


def test_renderer_failure_preserves_last_content_and_reports_component_error() -> None:
    observed = []

    def broken(_bundle):
        raise RuntimeError('secret backend detail')

    definition = _definition(broken)
    result = render_component_from_stores(
        component=definition.component('center_process'),
        configuration=definition.configuration,
        data_value=_data(),
        time_series_value=_time_series(),
        on_error=lambda component_key, error: observed.append(
            (component_key, type(error).__name__)
        ),
    )

    assert result.content is None
    assert result.preserve_content is True
    assert result.status.state('main') is ComponentRenderState.ERROR
    assert observed == [('center_process', 'RuntimeError')]


def test_state_is_resolved_independently_for_each_subcomponent() -> None:
    state = encode_component_state_snapshot(
        ComponentStateSnapshot(
            component_key='center_process',
            states={
                'main': ComponentProjectionState.STALE,
                'secondary': ComponentProjectionState.CONSTRUCTION,
            },
        )
    )
    definition = _definition(_rendered)
    ready = encode_render_status(
        ComponentRenderStatus(
            'center_process',
            {'main': ComponentRenderState.READY, 'secondary': ComponentRenderState.READY},
        )
    )

    assert (
        resolve_subcomponent_cover(
            component_key='center_process',
            subcomponent_key='main',
            state_value=state,
            render_status_value=ready,
        ).state
        is CoverState.STALE
    )
    assert (
        resolve_subcomponent_cover(
            component_key='center_process',
            subcomponent_key='secondary',
            state_value=state,
            render_status_value=ready,
        ).state
        is CoverState.CONSTRUCTION
    )
    assert initial_render_status(definition.component('center_process'))['states'] == {
        'main': 'waiting',
        'secondary': 'waiting',
    }


def test_stale_never_overrides_waiting_or_error_for_same_subcomponent() -> None:
    stale = encode_component_state_snapshot(
        ComponentStateSnapshot(
            component_key='center_process',
            states={
                'main': ComponentProjectionState.STALE,
                'secondary': ComponentProjectionState.STALE,
            },
        )
    )
    waiting = encode_render_status(
        ComponentRenderStatus(
            'center_process',
            {'main': ComponentRenderState.WAITING, 'secondary': ComponentRenderState.READY},
        )
    )
    error = encode_render_status(
        ComponentRenderStatus(
            'center_process',
            {'main': ComponentRenderState.ERROR, 'secondary': ComponentRenderState.READY},
        )
    )

    assert (
        resolve_subcomponent_cover(
            component_key='center_process',
            subcomponent_key='main',
            state_value=stale,
            render_status_value=waiting,
        ).state
        is CoverState.NONE
    )
    assert (
        resolve_subcomponent_cover(
            component_key='center_process',
            subcomponent_key='main',
            state_value=stale,
            render_status_value=error,
        ).state
        is CoverState.COMPONENT_ERROR
    )
