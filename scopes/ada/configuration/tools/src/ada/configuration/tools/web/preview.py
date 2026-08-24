from __future__ import annotations

from dash import html

from ada.configuration.tools.models import ToolConfiguration


def build_tool_history_preview(payload: dict[str, object]) -> object:
    configuration = ToolConfiguration.from_document(payload)
    component_count = len(configuration.components)
    subcomponent_count = sum(len(component.subcomponents) for component in configuration.components)
    source_count = len(configuration.sources)
    return html.Div(
        [
            _summary(
                (
                    ('Componentes', str(component_count)),
                    ('Subcomponentes', str(subcomponent_count)),
                    ('Fuentes', str(source_count)),
                )
            ),
            html.Div(
                _tool(configuration),
                className='atlanticus-manager__preview-tree',
            ),
        ],
        className='atlanticus-manager__preview-content',
    )


def _tool(tool: ToolConfiguration) -> object:
    badges = [_badge(f'Tipo: {tool.kind.value}')]
    if tool.operational_scope is not None:
        badges.append(_badge(f'Scope: {tool.operational_scope.value}'))
    return html.Section(
        [
            html.Header(
                [
                    html.Div(
                        [html.Strong(tool.display_name), html.Code(tool.tool_key)],
                        className='atlanticus-manager__preview-section-copy',
                    ),
                    html.Div(badges, className='atlanticus-manager__preview-badges'),
                ],
                className='atlanticus-manager__preview-section-heading',
            ),
            _sources(tool.sources),
            html.Div(
                [_component(component) for component in tool.components]
                if tool.components
                else html.P(
                    'Sin componentes configurados.',
                    className='atlanticus-manager__preview-empty',
                ),
                className='atlanticus-manager__preview-children',
            ),
        ],
        className='atlanticus-manager__preview-section',
    )


def _sources(sources) -> object:
    if not sources:
        return html.Div(
            'Sin fuentes configuradas.',
            className='atlanticus-manager__preview-detail',
        )
    return html.Div(
        [
            html.Div(
                [
                    html.Code(source.key.value),
                    html.Span(f'Vencimiento: {source.stale_after_seconds} s'),
                ],
                className='atlanticus-manager__preview-source',
            )
            for source in sources
        ],
        className='atlanticus-manager__preview-sources',
    )


def _component(component) -> object:
    badges = []
    if component.scope is not None:
        badges.append(_badge(f'Scope: {component.scope.value}'))
    if component.layout_role is not None:
        badges.append(_badge(f'Región: {component.layout_role.value}'))
    return html.Article(
        [
            html.Div(
                [html.Strong(component.display_name), html.Code(component.key)],
                className='atlanticus-manager__preview-entity-title',
            ),
            html.Div(badges, className='atlanticus-manager__preview-badges') if badges else None,
            html.Div(
                [_subcomponent(item) for item in component.subcomponents]
                if component.subcomponents
                else html.P(
                    'Sin subcomponentes.',
                    className='atlanticus-manager__preview-empty',
                ),
                className='atlanticus-manager__preview-subcomponents',
            ),
        ],
        className='atlanticus-manager__preview-entity',
    )


def _subcomponent(subcomponent) -> object:
    linked = ', '.join(subcomponent.linked_component_keys) or 'Sin vínculos'
    return html.Div(
        [
            html.Div(
                [html.Strong(subcomponent.display_name), html.Code(subcomponent.key)],
                className='atlanticus-manager__preview-entity-title',
            ),
            html.Small(
                f'Componentes vinculados: {linked}',
                className='atlanticus-manager__preview-detail',
            ),
        ],
        className='atlanticus-manager__preview-subcomponent',
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


def _badge(value: str) -> object:
    return html.Span(value, className='atlanticus-manager__preview-badge')
