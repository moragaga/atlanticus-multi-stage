from dash import dcc, html

from ada.configuration.kpis.models import KpiConfiguration
from ada.configuration.kpis.web.ids import (
    ADD_BINDING_ID,
    BINDING_CANCEL_ID,
    BINDING_DESTINATIONS_ID,
    BINDING_KEY_ID,
    BINDING_LATEST_ID,
    BINDING_MODAL_ID,
    BINDING_MODAL_TITLE_ID,
    BINDING_RESULT_ID,
    BINDING_SAVE_ID,
    BINDING_SERIES_HOURS_FIELD_ID,
    BINDING_SERIES_HOURS_ID,
    BINDING_SERIES_ID,
    BINDINGS_LIST_ID,
    CONFIGURATION_STORE_ID,
    DESTINATIONS_STORE_ID,
    EDITOR_ID,
    EDITOR_STORE_ID,
    MOUNT_STORE_ID,
    PROTECTED_DETAIL_ID,
    PROTECTED_ID,
    SAVE_BUTTON_ID,
    SAVE_RESULT_ID,
    SOURCE_REVISION_STORE_ID,
    TOOL_PROJECTION_REVISION_ID,
)
from ada.configuration.kpis.web.models import KpiAdminWebContext


def build_kpi_admin_configuration(context: KpiAdminWebContext) -> object:
    return html.Div(
        [
            dcc.Store(
                id=CONFIGURATION_STORE_ID,
                data=KpiConfiguration().to_document(),
                storage_type='memory',
            ),
            dcc.Store(id=SOURCE_REVISION_STORE_ID, data=None, storage_type='memory'),
            dcc.Store(id=DESTINATIONS_STORE_ID, data=None, storage_type='memory'),
            dcc.Store(id=MOUNT_STORE_ID, data=1, storage_type='memory'),
            dcc.Store(id=EDITOR_STORE_ID, data=None, storage_type='memory'),
            _runtime_context(context),
            _protected_state(context),
            html.Div(
                [
                    _toolbar(),
                    _bindings_section(),
                    _save_section(),
                ],
                id=EDITOR_ID,
                className='ada-kpis-admin__editor ada-kpis-admin__editor--hidden',
            ),
            _binding_modal(),
        ],
        className='ada-kpis-admin',
    )


def _runtime_context(context: KpiAdminWebContext) -> object:
    return html.Section(
        [
            html.Div(
                [html.Span('Fuente de verdad'), html.Strong(context.source_name)],
                className='ada-kpis-admin__runtime-source',
            ),
            html.Div(
                [html.Span('Proyección KPI'), html.Strong(context.projection_name)],
                className='ada-kpis-admin__runtime-source',
            ),
            html.Div(
                [
                    html.Span('Tool Projection'),
                    html.Code('—', id=TOOL_PROJECTION_REVISION_ID),
                ],
                className='ada-kpis-admin__runtime-source',
            ),
        ],
        className='ada-kpis-admin__runtime-context',
    )


def _protected_state(context: KpiAdminWebContext) -> object:
    return html.Section(
        [
            html.Div('KPI Configuration', className='ada-kpis-admin__protected-eyebrow'),
            html.H3('Primero configura y proyecta una herramienta ADA'),
            html.P(
                (
                    'KPI Configuration depende de la Tool Projection estable para resolver sus '
                    'destinos. No se usarán Source, History ni un baseline operacional como fallback.'
                ),
                id=PROTECTED_DETAIL_ID,
            ),
            dcc.Link(
                'Ir a Herramientas',
                href=context.tools_route,
                className='atlanticus-manager__button atlanticus-manager__button--primary',
            ),
        ],
        id=PROTECTED_ID,
        className='ada-kpis-admin__protected',
    )


def _toolbar() -> object:
    return html.Section(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Strong('KPIs configurados'),
                            html.Span(
                                (
                                    'Cada KPI puede alimentar uno o varios componentes proyectados. '
                                    'Latest y Series se configuran de forma independiente.'
                                ),
                                className='ada-kpis-admin__field-help',
                            ),
                        ],
                        className='ada-kpis-admin__toolbar-copy',
                    ),
                    html.Button(
                        'Agregar KPI',
                        id=ADD_BINDING_ID,
                        className='atlanticus-manager__button atlanticus-manager__button--secondary',
                    ),
                ],
                className='ada-kpis-admin__toolbar-row',
            )
        ],
        className='ada-kpis-admin__toolbar',
    )


def _bindings_section() -> object:
    return html.Section(
        [
            html.Div(
                [
                    html.H3('Bindings KPI'),
                    html.P(
                        'Los destinos disponibles provienen exclusivamente de la Tool Projection vigente.'
                    ),
                ],
                className='ada-kpis-admin__section-heading-copy',
            ),
            html.Div(id=BINDINGS_LIST_ID, className='ada-kpis-admin__bindings-list'),
        ],
        className='ada-kpis-admin__section',
    )


def _save_section() -> object:
    return html.Section(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H3('Borrador local'),
                            html.P(
                                'Guardar conserva el trabajo en el navegador. Publicar y proyectar siguen siendo acciones manuales del lifecycle.'
                            ),
                        ],
                        className='ada-kpis-admin__section-heading-copy',
                    ),
                    html.Button(
                        'Guardar borrador',
                        id=SAVE_BUTTON_ID,
                        className='atlanticus-manager__button atlanticus-manager__button--primary',
                    ),
                ],
                className='ada-kpis-admin__save-actions',
            ),
            html.Div(id=SAVE_RESULT_ID),
        ],
        className='ada-kpis-admin__section ada-kpis-admin__section--footer',
    )


def _binding_modal() -> object:
    return html.Div(
        [
            html.Button(
                id=BINDING_CANCEL_ID,
                className='ada-kpis-admin__modal-backdrop',
                **{'aria-label': 'Cerrar formulario'},
            ),
            html.Section(
                [
                    html.Header(
                        [
                            html.Div(
                                [
                                    html.P('KPI', className='ada-kpis-admin__modal-eyebrow'),
                                    html.H3('Agregar KPI', id=BINDING_MODAL_TITLE_ID),
                                ]
                            ),
                            html.Button(
                                '×',
                                id=BINDING_CANCEL_ID + '-header',
                                className='atlanticus-manager__icon-button',
                                title='Cerrar',
                            ),
                        ],
                        className='ada-kpis-admin__modal-header',
                    ),
                    html.Div(
                        [
                            _field(
                                'KPI key',
                                dcc.Input(
                                    id=BINDING_KEY_ID,
                                    type='text',
                                    placeholder='produccion_total',
                                    autoComplete='off',
                                ),
                                'Identidad estable del KPI. No se modifica al editar.',
                            ),
                            _field(
                                'Destinos',
                                dcc.Dropdown(
                                    id=BINDING_DESTINATIONS_ID,
                                    multi=True,
                                    options=[],
                                    placeholder='Selecciona uno o varios componentes',
                                ),
                                'Sólo se muestran componentes KPI de la Tool Projection estable.',
                            ),
                            html.Div(
                                [
                                    _channel(
                                        'Latest',
                                        BINDING_LATEST_ID,
                                        'Entrega el valor actual del KPI.',
                                    ),
                                    _channel(
                                        'Series',
                                        BINDING_SERIES_ID,
                                        'Entrega la serie temporal del KPI.',
                                    ),
                                ],
                                className='ada-kpis-admin__channels',
                            ),
                            html.Div(
                                _field(
                                    'Horas de serie',
                                    dcc.Input(
                                        id=BINDING_SERIES_HOURS_ID,
                                        type='number',
                                        min=1,
                                        step=1,
                                        value=24,
                                    ),
                                    'Sólo aplica cuando Series está habilitado.',
                                ),
                                id=BINDING_SERIES_HOURS_FIELD_ID,
                                className='ada-kpis-admin__series-hours ada-kpis-admin__series-hours--hidden',
                            ),
                            html.Div(id=BINDING_RESULT_ID),
                        ],
                        className='ada-kpis-admin__modal-body',
                    ),
                    html.Footer(
                        [
                            html.Button(
                                'Cancelar',
                                id=BINDING_CANCEL_ID + '-footer',
                                className='atlanticus-manager__button atlanticus-manager__button--secondary',
                            ),
                            html.Button(
                                'Guardar KPI',
                                id=BINDING_SAVE_ID,
                                className='atlanticus-manager__button atlanticus-manager__button--primary',
                            ),
                        ],
                        className='ada-kpis-admin__modal-actions',
                    ),
                ],
                className='ada-kpis-admin__modal-dialog',
            ),
        ],
        id=BINDING_MODAL_ID,
        className='ada-kpis-admin__modal',
    )


def _field(label: str, control: object, help_text: str) -> object:
    return html.Label(
        [html.Span(label), control, html.Small(help_text, className='ada-kpis-admin__field-help')],
        className='ada-kpis-admin__field',
    )


def _channel(label: str, control_id: str, help_text: str) -> object:
    return html.Label(
        [
            dcc.Checklist(
                id=control_id,
                options=[{'label': label, 'value': 'enabled'}],
                value=[],
                className='ada-kpis-admin__channel-toggle',
            ),
            html.Small(help_text, className='ada-kpis-admin__field-help'),
        ],
        className='ada-kpis-admin__channel',
    )
