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
    resolve_component_cover,
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


def test_render_waits_until_all_required_projections_are_available() -> None:
    calls = []
    definition = _definition(lambda bundle: calls.append(bundle) or 'rendered')

    result = render_component_from_stores(
        component=definition.component('center_process'),
        configuration=definition.configuration,
        data_value=_data(),
        time_series_value=None,
    )

    assert result.status.state is ComponentRenderState.WAITING
    assert result.preserve_content is True
    assert calls == []


def test_render_builds_bundle_and_hydrates_time_axis_before_calling_developer() -> None:
    observed = []
    definition = _definition(lambda bundle: observed.append(bundle) or 'rendered')

    result = render_component_from_stores(
        component=definition.component('center_process'),
        configuration=definition.configuration,
        data_value=_data(),
        time_series_value=_time_series(),
    )

    assert result.content == 'rendered'
    assert result.preserve_content is False
    assert result.status.state is ComponentRenderState.READY
    assert observed[0].data['kpi'] == 87
    assert len(observed[0].time_series[1].axis.utc) == 6
    assert observed[0].time_series[1].series['ley'] == (1, 2, 3, 4, 5, 6)


def test_renderer_failure_preserves_last_content_and_isolated_error_status() -> None:
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
    assert result.status.state is ComponentRenderState.ERROR
    assert observed == [('center_process', 'RuntimeError')]


def test_time_series_contract_mismatch_is_isolated_before_renderer() -> None:
    calls = []
    definition = _definition(lambda bundle: calls.append(bundle) or 'rendered')

    result = render_component_from_stores(
        component=definition.component('center_process'),
        configuration=definition.configuration,
        data_value=_data(),
        time_series_value=_time_series(key='unexpected'),
    )

    assert result.status.state is ComponentRenderState.ERROR
    assert result.preserve_content is True
    assert calls == []


def test_state_changes_do_not_require_render_and_stale_only_applies_after_ready() -> None:
    stale = encode_component_state_snapshot(
        ComponentStateSnapshot(
            component_key='center_process',
            state=ComponentProjectionState.STALE,
        )
    )

    waiting_cover = resolve_component_cover(
        component_key='center_process',
        state_value=stale,
        render_status_value=initial_render_status('center_process'),
    )
    ready_cover = resolve_component_cover(
        component_key='center_process',
        state_value=stale,
        render_status_value=encode_render_status(
            ComponentRenderStatus('center_process', ComponentRenderState.READY)
        ),
    )

    assert waiting_cover.state is CoverState.NONE
    assert ready_cover.state is CoverState.STALE


def test_component_error_overrides_stale_and_source_unavailable_maps_to_source_error() -> None:
    stale = encode_component_state_snapshot(
        ComponentStateSnapshot(
            component_key='center_process',
            state=ComponentProjectionState.STALE,
        )
    )
    unavailable = encode_component_state_snapshot(
        ComponentStateSnapshot(
            component_key='center_process',
            state=ComponentProjectionState.UNAVAILABLE,
        )
    )
    error_status = encode_render_status(
        ComponentRenderStatus('center_process', ComponentRenderState.ERROR)
    )
    ready_status = encode_render_status(
        ComponentRenderStatus('center_process', ComponentRenderState.READY)
    )

    assert (
        resolve_component_cover(
            component_key='center_process',
            state_value=stale,
            render_status_value=error_status,
        ).state
        is CoverState.COMPONENT_ERROR
    )
    assert (
        resolve_component_cover(
            component_key='center_process',
            state_value=unavailable,
            render_status_value=ready_status,
        ).state
        is CoverState.SOURCE_ERROR
    )
    assert (
        resolve_component_cover(
            component_key='center_process',
            state_value=stale,
            render_status_value=ready_status,
        ).state
        is CoverState.STALE
    )
