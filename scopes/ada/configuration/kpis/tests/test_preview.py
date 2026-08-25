from ada.configuration.kpis import KpiBinding, KpiConfiguration
from ada.configuration.kpis.web.preview import build_kpi_history_preview


def _text(value: object) -> str:
    if value is None:
        return ''
    if isinstance(value, (str, int, float)):
        return str(value)
    children = getattr(value, 'children', None)
    if isinstance(children, (list, tuple)):
        return ' '.join(_text(item) for item in children)
    return _text(children)


def test_history_preview_renders_binding_channels_and_destinations() -> None:
    configuration = KpiConfiguration(
        bindings=(
            KpiBinding(
                key='production_total',
                destination_keys=('global_indicators', 'molienda'),
                latest_enabled=True,
                series_enabled=True,
                series_hours=24,
            ),
            KpiBinding(
                key='disabled_kpi',
                destination_keys=('time_status',),
                latest_enabled=False,
                series_enabled=False,
            ),
        )
    )

    preview = build_kpi_history_preview(configuration.to_document())
    text = _text(preview)

    assert 'KPIs 2' in text
    assert 'Activos 1' in text
    assert 'Latest 1' in text
    assert 'Series 1' in text
    assert 'production_total' in text
    assert 'global_indicators' in text
    assert 'molienda' in text
    assert 'Series: 24 h' in text
    assert 'disabled_kpi' in text
    assert 'Desactivado' in text
