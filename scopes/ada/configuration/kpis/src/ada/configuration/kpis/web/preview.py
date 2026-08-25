from dash import html

from ada.configuration.kpis.models import KpiConfiguration


def build_kpi_history_preview(payload: dict[str, object]) -> object:
    configuration = KpiConfiguration.from_document(payload)
    active = sum(binding.enabled for binding in configuration.bindings)
    latest = sum(binding.latest_enabled for binding in configuration.bindings)
    series = sum(binding.series_enabled for binding in configuration.bindings)
    return html.Div(
        [
            _summary(
                (
                    ('KPIs', str(len(configuration.bindings))),
                    ('Activos', str(active)),
                    ('Latest', str(latest)),
                    ('Series', str(series)),
                )
            ),
            html.Div(
                [_binding(binding) for binding in configuration.bindings]
                if configuration.bindings
                else html.P(
                    'Sin KPIs configurados.',
                    className='atlanticus-manager__preview-empty',
                ),
                className='atlanticus-manager__preview-tree',
            ),
        ],
        className='atlanticus-manager__preview-content',
    )


def _binding(binding) -> object:
    channels = []
    if binding.latest_enabled:
        channels.append(_badge('Latest'))
    if binding.series_enabled:
        channels.append(_badge(f'Series: {binding.series_hours} h'))
    if not binding.enabled:
        channels.append(_badge('Desactivado'))
    return html.Article(
        [
            html.Header(
                [
                    html.Div(
                        [html.Strong(binding.key), html.Code(binding.key)],
                        className='atlanticus-manager__preview-section-copy',
                    ),
                    html.Div(channels, className='atlanticus-manager__preview-badges'),
                ],
                className='atlanticus-manager__preview-section-heading',
            ),
            html.Div(
                [
                    html.Div(
                        [html.Code(destination)],
                        className='atlanticus-manager__preview-subcomponent',
                    )
                    for destination in binding.destination_keys
                ],
                className='atlanticus-manager__preview-children',
            ),
        ],
        className='atlanticus-manager__preview-section',
    )


def _summary(items: tuple[tuple[str, str], ...]) -> object:
    return html.Div(
        [
            html.Div(
                [html.Small(label), html.Strong(value)],
                className='atlanticus-manager__preview-summary-item',
            )
            for label, value in items
        ],
        className='atlanticus-manager__preview-summary',
    )


def _badge(label: str) -> object:
    return html.Span(label, className='atlanticus-manager__preview-badge')
