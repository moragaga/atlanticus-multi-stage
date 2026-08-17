# Espejo comentado: vista completa de Operaciones Integradas que coordina header, alarmas y body mediante un único estado de presentación.
from __future__ import annotations

from dash import html

from .errors import IntegratedOperationsLayoutError
from .models import IntegratedOperationsView


def build_integrated_operations_view(
    *,
    header_content: object,
    mine_alarm_pills: object,
    plant_alarm_pills: object,
    body_content: object,
    view: IntegratedOperationsView = IntegratedOperationsView.OVERVIEW,
    view_id: str | None = None,
    class_name: str | None = None,
) -> html.Div:
    _validate_view(view)
    _validate_view_id(view_id)
    classes = ' '.join(
        item
        for item in (
            'ada-io-view',
            class_name,
        )
        if item
    )
    attributes = {
        'className': classes,
        'data-ada-io-view-root': 'integrated-operations',
        'data-ada-io-view': view.value,
    }
    if view_id is not None:
        attributes['id'] = view_id

    return html.Div(
        [
            html.Div(header_content, className='ada-io-view__header'),
            html.Div(
                [
                    _build_alarm_scope('mine', mine_alarm_pills),
                    _build_alarm_scope('plant', plant_alarm_pills),
                ],
                className='ada-io-view__alarms',
            ),
            html.Div(
                [
                    body_content,
                    _build_overview_controls(),
                ],
                className='ada-io-view__body',
            ),
            _build_zoom_controls(),
        ],
        **attributes,
    )


def _build_alarm_scope(scope: str, content: object) -> html.Div:
    return html.Div(
        content,
        className=f'ada-io-view__alarm-scope ada-io-view__alarm-scope--{scope}',
        **{'data-ada-io-view-scope': scope},
    )


def _build_overview_controls() -> html.Div:
    return html.Div(
        [
            _build_button(
                target=IntegratedOperationsView.MINE,
                label='MINA',
                title='Ampliar Mina',
                class_name='ada-io-view__overview-button ada-io-view__overview-button--mine',
            ),
            _build_button(
                target=IntegratedOperationsView.PLANT,
                label='PLANTA',
                title='Ampliar Planta',
                class_name='ada-io-view__overview-button ada-io-view__overview-button--plant',
            ),
        ],
        className='ada-io-view__overview-controls',
        role='group',
        **{'aria-label': 'Ampliar área de Operaciones Integradas'},
    )


def _build_zoom_controls() -> html.Div:
    return html.Div(
        [
            _build_button(
                target=IntegratedOperationsView.OVERVIEW,
                label='×',
                title='Cerrar vista ampliada',
                class_name='ada-io-view__close',
            ),
            _build_button(
                target=IntegratedOperationsView.MINE,
                label='MINA',
                title='Ver Mina',
                class_name='ada-io-view__side ada-io-view__side--mine',
            ),
            _build_button(
                target=IntegratedOperationsView.PLANT,
                label='PLANTA',
                title='Ver Planta',
                class_name='ada-io-view__side ada-io-view__side--plant',
            ),
        ],
        className='ada-io-view__zoom-controls',
        **{'data-ada-io-view-controls': 'true'},
    )


def _build_button(
    *,
    target: IntegratedOperationsView,
    label: str,
    title: str,
    class_name: str,
) -> html.Button:
    return html.Button(
        label,
        type='button',
        title=title,
        className=class_name,
        **{
            'aria-label': title,
            'data-ada-io-target-view': target.value,
        },
    )


def _validate_view(view: IntegratedOperationsView) -> None:
    if not isinstance(view, IntegratedOperationsView):
        raise IntegratedOperationsLayoutError(f'Invalid integrated operations view: {view!r}')


def _validate_view_id(view_id: str | None) -> None:
    if view_id is not None and (not isinstance(view_id, str) or not view_id.strip()):
        raise IntegratedOperationsLayoutError(
            f'Invalid integrated operations view id: {view_id!r}'
        )
