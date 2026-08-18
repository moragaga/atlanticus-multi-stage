from ada.contracts.tool_manifest import ProcessBodySection
from process_base.tool import COMPOSITION, MANIFEST


def test_process_base_declares_portable_process_geometry() -> None:
    roles = {component.layout_role: component.key for component in MANIFEST.children('body')}

    assert roles == {
        ProcessBodySection.LEFT: 'upstream',
        ProcessBodySection.CENTER: 'main_process',
        ProcessBodySection.RIGHT: 'downstream',
        ProcessBodySection.BOTTOM: 'trends',
    }
    assert len(COMPOSITION.mount.subcomponent_slots) == 8
    assert COMPOSITION.dashboard.manifest is MANIFEST


def test_process_base_contains_heavy_time_series_contracts_without_layout_knowledge() -> None:
    center = COMPOSITION.dashboard.configuration.projection('main_process')
    trends = COMPOSITION.dashboard.configuration.projection('trends')

    assert tuple((item.key, item.hours) for item in center.time_series) == (
        ('primary', 1),
        ('recovery', 5),
    )
    assert tuple((item.key, item.hours) for item in trends.time_series) == (('overview', 24),)
    assert COMPOSITION.dashboard.configuration.time_series.step_seconds == 60


def test_process_base_graph_renderer_is_responsive_to_card_boundary() -> None:
    from datetime import UTC, datetime, timedelta

    from ada.features.dashboard import ComponentBundle, TimeAxis, TimeSeriesWindow
    from process_base.definition import _render_card

    start = datetime(2026, 8, 17, 20, 0, tzinfo=UTC)
    axis = TimeAxis(
        utc=(start, start + timedelta(minutes=1)),
        local=(start, start + timedelta(minutes=1)),
        labels=('20:00', '20:01'),
        timezone='UTC',
    )
    window = TimeSeriesWindow(
        hours=1,
        start_utc=start,
        end_utc=start + timedelta(hours=1),
        step_seconds=60,
        axis=axis,
        series={'primary': (73.0, 74.0)},
    )
    content = _render_card(
        ComponentBundle(component_key='main_process', time_series={1: window}),
        subcomponent='primary',
        value=73.0,
    )
    graph = content.to_plotly_json()['props']['children'][1]
    props = graph.to_plotly_json()['props']

    assert props['figure']['layout'].get('height') is None
    assert props['figure']['layout']['autosize'] is True
    assert props['style'] == {'height': '100%', 'minHeight': 0}
    assert props['config']['responsive'] is True
