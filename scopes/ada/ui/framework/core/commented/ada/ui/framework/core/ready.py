# Espejo comentado del gate de readiness inicial de página.
# Ready significa render controlado; no implica que los datos sean válidos.
from __future__ import annotations

import re
from collections.abc import Sequence

from dash import html
from dash.development.base_component import Component

_READY_NAME = re.compile(r'^[a-z][a-z0-9-]*$')

ReadyContent = Component | Sequence[Component]


def ready_attributes(name: str, *, ready: bool) -> dict[str, str]:
    normalized = _normalize_ready_name(name)
    return {
        'data-ready': 'true' if ready else 'false',
        'data-ready-name': normalized,
    }


def build_ready_scope(
    *,
    content: ReadyContent,
    required: tuple[str, ...],
    loader: Component | None = None,
    timeout_ms: int = 30_000,
    class_name: str | None = None,
) -> html.Div:
    required_names = tuple(_normalize_ready_name(name) for name in required)
    if not required_names:
        raise ValueError('Ready scope requires at least one readiness name')
    if len(required_names) != len(set(required_names)):
        raise ValueError('Ready scope contains duplicate readiness names')
    if timeout_ms < 1_000:
        raise ValueError('Ready scope timeout must be at least 1000 ms')

    return html.Div(
        className=_join_classes('ada-page-ready', 'is-loading', class_name),
        **{
            'data-page-ready': 'true',
            'data-ready-state': 'loading',
            'data-ready-required': ','.join(required_names),
            'data-ready-timeout-ms': str(timeout_ms),
        },
        children=[
            html.Div(
                className='ada-page-ready__overlay',
                children=[loader or _build_default_loader()],
            ),
            html.Div(
                className='ada-page-ready__content',
                children=content,
            ),
        ],
    )


def _build_default_loader() -> Component:
    return html.Div(
        className='ada-page-ready__loader',
        children=[
            html.Div(className='ada-page-ready__spinner', **{'aria-hidden': 'true'}),
            html.P(
                'Cargando...',
                className='ada-page-ready__message',
                **{'data-page-ready-message': 'true'},
            ),
        ],
    )


def _normalize_ready_name(value: str) -> str:
    normalized = value.strip()
    if not _READY_NAME.fullmatch(normalized):
        raise ValueError(f'Invalid readiness name: {value!r}')
    return normalized


def _join_classes(*values: str | None) -> str:
    return ' '.join(value.strip() for value in values if value and value.strip())
