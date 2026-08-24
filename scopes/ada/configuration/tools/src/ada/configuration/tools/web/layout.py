from __future__ import annotations

from dash import dcc, html

from ada.configuration.tools.web.ids import (
    ADD_COMPONENT_ID,
    ADD_SUBCOMPONENT_ID,
    APPLICATION_KEY_ID,
    COMPONENT_CANCEL_ID,
    COMPONENT_EDITOR_STORE_ID,
    COMPONENT_MODAL_ID,
    COMPONENT_MODAL_RESULT_ID,
    COMPONENT_MODAL_TITLE_ID,
    COMPONENT_NAME_ID,
    COMPONENT_PLACEMENT_FIELD_ID,
    COMPONENT_PLACEMENT_ID,
    COMPONENT_SAVE_ID,
    COMPONENT_SCOPE_FIELD_ID,
    COMPONENT_SCOPE_ID,
    COMPONENTS_LIST_ID,
    CONFIGURATION_STORE_ID,
    CREATE_BUTTON_ID,
    CREATE_CANCEL_ID,
    CREATE_KIND_ID,
    CREATE_MODAL_ID,
    CREATE_NAME_ID,
    CREATE_OPEN_ID,
    CREATE_RESULT_ID,
    DISPATCH_FRESHNESS_FIELD_ID,
    DISPATCH_FRESHNESS_ID,
    DRAFT_LOAD_SIGNAL_ID,
    IMPORT_RESULT_ID,
    IMPORT_UPLOAD_ID,
    PI_FRESHNESS_FIELD_ID,
    PI_FRESHNESS_ID,
    PROJECTION_NAME_ID,
    REFERENCE_ID,
    SAVE_BUTTON_ID,
    SAVE_RESULT_ID,
    SOURCE_NAME_ID,
    SOURCE_REVISION_STORE_ID,
    SOURCES_ID,
    STRUCTURE_RESULT_ID,
    STRUCTURE_STORE_ID,
    SUBCOMPONENT_CANCEL_ID,
    SUBCOMPONENT_EDITOR_STORE_ID,
    SUBCOMPONENT_LINKED_FIELD_ID,
    SUBCOMPONENT_LINKED_ID,
    SUBCOMPONENT_MODAL_ID,
    SUBCOMPONENT_MODAL_RESULT_ID,
    SUBCOMPONENT_MODAL_TITLE_ID,
    SUBCOMPONENT_NAME_ID,
    SUBCOMPONENT_PARENT_ID,
    SUBCOMPONENT_SAVE_ID,
    SUBCOMPONENTS_LIST_ID,
    TOOL_KEY_ID,
    TOOL_KIND_ID,
    TOOL_NAME_ID,
    TOOL_SCOPE_ID,
)
from ada.configuration.tools.web.models import ToolAdminWebContext


def build_tool_admin_configuration(context: ToolAdminWebContext) -> object:
    return html.Div(
        [
            dcc.Store(id=CONFIGURATION_STORE_ID, data=None, storage_type='memory'),
            dcc.Store(
                id=SOURCE_REVISION_STORE_ID,
                data=None,
                storage_type='memory',
            ),
            dcc.Store(id=STRUCTURE_STORE_ID, data=[], storage_type='memory'),
            dcc.Store(id=DRAFT_LOAD_SIGNAL_ID, data=0, storage_type='memory'),
            dcc.Store(id=COMPONENT_EDITOR_STORE_ID, storage_type='memory'),
            dcc.Store(id=SUBCOMPONENT_EDITOR_STORE_ID, storage_type='memory'),
            _runtime_context(context),
            _tool_toolbar(),
            _general_section(),
            _sources_section(),
            _structure_section(),
            _reference_section(context),
            _tool_modal(),
            _component_modal(),
            _subcomponent_modal(),
        ],
        className='ada-tools-admin',
    )


def _runtime_context(context: ToolAdminWebContext) -> object:
    return html.Section(
        [
            html.Div(
                [
                    html.Span('Fuente de verdad'),
                    html.Strong(context.source_name, id=SOURCE_NAME_ID),
                ],
                className='ada-tools-admin__runtime-source',
            ),
            html.Div(
                [
                    html.Span('Proyección'),
                    html.Strong(context.projection_name, id=PROJECTION_NAME_ID),
                ],
                className='ada-tools-admin__runtime-source',
            ),
            html.Div(
                [
                    dcc.Upload(
                        id=IMPORT_UPLOAD_ID,
                        children=html.Button(
                            'Importar configuración de herramienta',
                            className=(
                                'atlanticus-manager__button atlanticus-manager__button--secondary'
                            ),
                        ),
                        multiple=False,
                    ),
                    html.Span(
                        (
                            'El archivo se carga como borrador local y no modifica '
                            'la fuente de verdad.'
                        ),
                        className='ada-tools-admin__runtime-help',
                    ),
                    html.Div(id=IMPORT_RESULT_ID),
                ],
                className='ada-tools-admin__import',
            ),
        ],
        className='ada-tools-admin__runtime-context',
    )


def _tool_toolbar() -> object:
    return html.Section(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Strong('Configuración única de herramienta'),
                            html.Span(
                                (
                                    'Este despliegue ADA tiene una sola herramienta. '
                                    'La configuración define su scope, fuentes y estructura.'
                                ),
                                className='ada-tools-admin__field-help',
                            ),
                        ],
                        className='ada-tools-admin__toolbar-copy',
                    ),
                    html.Button(
                        'Configurar herramienta',
                        id=CREATE_OPEN_ID,
                        className=(
                            'atlanticus-manager__button atlanticus-manager__button--secondary'
                        ),
                    ),
                ],
                className='ada-tools-admin__toolbar-row',
            ),
        ],
        className='ada-tools-admin__toolbar',
    )


def _tool_modal() -> object:
    return html.Div(
        [
            html.Button(
                id=CREATE_CANCEL_ID,
                className='ada-tools-admin__modal-backdrop',
                **{'aria-label': 'Cerrar formulario'},
            ),
            html.Section(
                [
                    html.Header(
                        [
                            html.Div(
                                [
                                    html.P(
                                        'Herramienta',
                                        className='ada-tools-admin__modal-eyebrow',
                                    ),
                                    html.H3('Configurar herramienta'),
                                ]
                            ),
                            html.Button(
                                '×',
                                id=CREATE_CANCEL_ID + '-header',
                                className='atlanticus-manager__icon-button',
                                title='Cerrar',
                            ),
                        ],
                        className='ada-tools-admin__modal-header',
                    ),
                    html.Div(
                        [
                            _field(
                                'Nombre',
                                dcc.Input(
                                    id=CREATE_NAME_ID,
                                    type='text',
                                    placeholder='Nombre visible de la herramienta',
                                    autoComplete='off',
                                ),
                                'El identificador estable se genera automáticamente.',
                            ),
                            _field(
                                'Tipo',
                                dcc.Dropdown(
                                    id=CREATE_KIND_ID,
                                    value=None,
                                    clearable=False,
                                    searchable=False,
                                    placeholder='Selecciona el tipo',
                                    options=[
                                        {
                                            'label': 'Operaciones Integradas',
                                            'value': 'integrated_operations',
                                        },
                                        {'label': 'Process', 'value': 'process'},
                                    ],
                                ),
                                'El tipo define las reglas estructurales que ADA aplicará.',
                            ),
                            html.Div(id=CREATE_RESULT_ID),
                        ],
                        className='ada-tools-admin__modal-body',
                    ),
                    html.Footer(
                        [
                            html.Button(
                                'Cancelar',
                                id=CREATE_CANCEL_ID + '-footer',
                                className=(
                                    'atlanticus-manager__button '
                                    'atlanticus-manager__button--secondary'
                                ),
                            ),
                            html.Button(
                                'Crear configuración',
                                id=CREATE_BUTTON_ID,
                                className=(
                                    'atlanticus-manager__button atlanticus-manager__button--primary'
                                ),
                            ),
                        ],
                        className='ada-tools-admin__modal-actions',
                    ),
                ],
                className='ada-tools-admin__modal-dialog',
            ),
        ],
        id=CREATE_MODAL_ID,
        className='ada-tools-admin__modal',
    )


def _general_section() -> object:
    return html.Section(
        [
            _section_heading(
                'Información general',
                'Define cómo se identifica la herramienta. Los IDs se generan automáticamente.',
            ),
            html.Div(
                [
                    _field(
                        'Nombre',
                        dcc.Input(id=TOOL_NAME_ID, type='text'),
                        'Nombre visible que verá el usuario en ADA.',
                    ),
                    _reference_field(
                        'Identificador',
                        TOOL_KEY_ID,
                        'Se crea una vez y permanece estable aunque cambie el nombre.',
                    ),
                    _reference_field(
                        'Aplicación',
                        APPLICATION_KEY_ID,
                        'Contrato de aplicación que interpreta esta configuración.',
                    ),
                    _reference_field(
                        'Tipo',
                        TOOL_KIND_ID,
                        'Determina las reglas estructurales que ADA genera automáticamente.',
                    ),
                    _field(
                        'Área de la herramienta',
                        dcc.Dropdown(
                            id=TOOL_SCOPE_ID,
                            clearable=False,
                            searchable=False,
                            options=[
                                {'label': 'Mina y Planta', 'value': 'global'},
                                {'label': 'Mina', 'value': 'mine'},
                                {'label': 'Planta', 'value': 'plant'},
                            ],
                        ),
                        (
                            'Operaciones Integradas cubre Mina y Planta. '
                            'Process usa un único ámbito operacional.'
                        ),
                    ),
                ],
                className='ada-tools-admin__general-grid',
            ),
        ],
        className='ada-tools-admin__section',
    )


def _sources_section() -> object:
    return html.Section(
        [
            _section_heading(
                'Fuentes y freshness',
                (
                    'Selecciona solo las fuentes que participan en la herramienta. '
                    'El freshness define cuándo una fuente se considera desactualizada.'
                ),
            ),
            dcc.Checklist(
                id=SOURCES_ID,
                options=[
                    {'label': 'PI', 'value': 'pi'},
                    {'label': 'Dispatch', 'value': 'dispatch'},
                ],
                inline=True,
                className='ada-tools-admin__source-selector',
            ),
            html.Div(
                [
                    html.Div(
                        _field(
                            'PI · freshness',
                            dcc.Input(id=PI_FRESHNESS_ID, type='number', min=1, step=1),
                            'Segundos máximos sin actualización antes de marcar PI como stale.',
                        ),
                        id=PI_FRESHNESS_FIELD_ID,
                        className='ada-tools-admin__source-field',
                    ),
                    html.Div(
                        _field(
                            'Dispatch · freshness',
                            dcc.Input(
                                id=DISPATCH_FRESHNESS_ID,
                                type='number',
                                min=1,
                                step=1,
                            ),
                            (
                                'Segundos máximos sin actualización antes de marcar '
                                'Dispatch como stale.'
                            ),
                        ),
                        id=DISPATCH_FRESHNESS_FIELD_ID,
                        className='ada-tools-admin__source-field',
                    ),
                ],
                className='ada-tools-admin__source-grid',
            ),
        ],
        className='ada-tools-admin__section',
    )


def _structure_section() -> object:
    return html.Div(
        [
            html.Section(
                [
                    html.Div(
                        [
                            _section_heading(
                                'Componentes',
                                (
                                    'Son las unidades principales del body. '
                                    'Su ID se genera automáticamente al crearlas.'
                                ),
                            ),
                            html.Button(
                                '+ Componente',
                                id=ADD_COMPONENT_ID,
                                className=(
                                    'atlanticus-manager__button '
                                    'atlanticus-manager__button--secondary'
                                ),
                            ),
                        ],
                        className='ada-tools-admin__section-heading-row',
                    ),
                    html.Div(id=COMPONENTS_LIST_ID, className='ada-tools-admin__structure-list'),
                ],
                className='ada-tools-admin__section',
            ),
            html.Section(
                [
                    html.Div(
                        [
                            _section_heading(
                                'Subcomponentes',
                                (
                                    'Se crean dentro de un componente. '
                                    'Los vínculos compartidos solo se declaran cuando existen.'
                                ),
                            ),
                            html.Button(
                                '+ Subcomponente',
                                id=ADD_SUBCOMPONENT_ID,
                                className=(
                                    'atlanticus-manager__button '
                                    'atlanticus-manager__button--secondary'
                                ),
                            ),
                        ],
                        className='ada-tools-admin__section-heading-row',
                    ),
                    html.Div(
                        id=SUBCOMPONENTS_LIST_ID,
                        className='ada-tools-admin__structure-list',
                    ),
                ],
                className='ada-tools-admin__section',
            ),
            html.Div(id=STRUCTURE_RESULT_ID),
        ],
        className='ada-tools-admin__structure',
    )


def _reference_section(context: ToolAdminWebContext) -> object:
    return html.Section(
        [
            html.Div(id=REFERENCE_ID),
            html.Div(
                [
                    html.Div(id=SAVE_RESULT_ID),
                    html.Button(
                        'Guardar borrador',
                        id=SAVE_BUTTON_ID,
                        className=(
                            'atlanticus-manager__button atlanticus-manager__button--primary'
                        ),
                    ),
                ],
                className='ada-tools-admin__save-actions',
            ),
        ],
        className='ada-tools-admin__section ada-tools-admin__section--footer',
    )


def _component_modal() -> object:
    return html.Div(
        [
            html.Button(
                id=COMPONENT_CANCEL_ID,
                className='ada-tools-admin__modal-backdrop',
                **{'aria-label': 'Cerrar formulario de componente'},
            ),
            html.Section(
                [
                    html.Header(
                        [
                            html.Div(
                                [
                                    html.P(
                                        'Estructura',
                                        className='ada-tools-admin__modal-eyebrow',
                                    ),
                                    html.H3(id=COMPONENT_MODAL_TITLE_ID),
                                ]
                            ),
                            html.Button(
                                '×',
                                id=COMPONENT_CANCEL_ID + '-header',
                                className='atlanticus-manager__icon-button',
                                title='Cerrar',
                            ),
                        ],
                        className='ada-tools-admin__modal-header',
                    ),
                    html.Div(
                        [
                            _field(
                                'Nombre del componente',
                                dcc.Input(id=COMPONENT_NAME_ID, type='text'),
                                'El ID se genera automáticamente a partir del nombre al crear.',
                            ),
                            html.Div(
                                _field(
                                    'Área',
                                    dcc.Dropdown(
                                        id=COMPONENT_SCOPE_ID,
                                        clearable=False,
                                        searchable=False,
                                        options=[
                                            {'label': 'Mina', 'value': 'mine'},
                                            {'label': 'Planta', 'value': 'plant'},
                                        ],
                                    ),
                                    'Ubica el componente en Mina o Planta.',
                                ),
                                id=COMPONENT_SCOPE_FIELD_ID,
                            ),
                            html.Div(
                                _field(
                                    'Ubicación en Process',
                                    dcc.Dropdown(
                                        id=COMPONENT_PLACEMENT_ID,
                                        clearable=False,
                                        searchable=False,
                                        options=[
                                            {'label': 'Proceso principal', 'value': 'center'},
                                            {'label': 'Aguas arriba', 'value': 'left'},
                                            {'label': 'Aguas abajo', 'value': 'right'},
                                            {'label': 'Inferior / especial', 'value': 'bottom'},
                                        ],
                                    ),
                                    'Define el rol visual del componente dentro de Process.',
                                ),
                                id=COMPONENT_PLACEMENT_FIELD_ID,
                            ),
                            html.Div(id=COMPONENT_MODAL_RESULT_ID),
                        ],
                        className='ada-tools-admin__modal-body',
                    ),
                    html.Footer(
                        [
                            html.Button(
                                'Cancelar',
                                id=COMPONENT_CANCEL_ID + '-footer',
                                className=(
                                    'atlanticus-manager__button '
                                    'atlanticus-manager__button--secondary'
                                ),
                            ),
                            html.Button(
                                'Guardar componente',
                                id=COMPONENT_SAVE_ID,
                                className=(
                                    'atlanticus-manager__button atlanticus-manager__button--primary'
                                ),
                            ),
                        ],
                        className='ada-tools-admin__modal-actions',
                    ),
                ],
                className='ada-tools-admin__modal-dialog',
            ),
        ],
        id=COMPONENT_MODAL_ID,
        className='ada-tools-admin__modal',
    )


def _subcomponent_modal() -> object:
    return html.Div(
        [
            html.Button(
                id=SUBCOMPONENT_CANCEL_ID,
                className='ada-tools-admin__modal-backdrop',
                **{'aria-label': 'Cerrar formulario de subcomponente'},
            ),
            html.Section(
                [
                    html.Header(
                        [
                            html.Div(
                                [
                                    html.P(
                                        'Estructura',
                                        className='ada-tools-admin__modal-eyebrow',
                                    ),
                                    html.H3(id=SUBCOMPONENT_MODAL_TITLE_ID),
                                ]
                            ),
                            html.Button(
                                '×',
                                id=SUBCOMPONENT_CANCEL_ID + '-header',
                                className='atlanticus-manager__icon-button',
                                title='Cerrar',
                            ),
                        ],
                        className='ada-tools-admin__modal-header',
                    ),
                    html.Div(
                        [
                            _field(
                                'Componente',
                                dcc.Dropdown(
                                    id=SUBCOMPONENT_PARENT_ID,
                                    clearable=False,
                                    searchable=True,
                                ),
                                'Selecciona el componente al que pertenece.',
                            ),
                            _field(
                                'Nombre del subcomponente',
                                dcc.Input(id=SUBCOMPONENT_NAME_ID, type='text'),
                                'El ID runtime se forma automáticamente con componente y nombre.',
                            ),
                            html.Div(
                                _field(
                                    'Compartido con',
                                    dcc.Dropdown(
                                        id=SUBCOMPONENT_LINKED_ID,
                                        multi=True,
                                        searchable=True,
                                        placeholder='Sin vínculos compartidos',
                                    ),
                                    (
                                        'Usa esta opción solo cuando una misma card pertenece '
                                        'a más de un componente.'
                                    ),
                                ),
                                id=SUBCOMPONENT_LINKED_FIELD_ID,
                            ),
                            html.Div(id=SUBCOMPONENT_MODAL_RESULT_ID),
                        ],
                        className='ada-tools-admin__modal-body',
                    ),
                    html.Footer(
                        [
                            html.Button(
                                'Cancelar',
                                id=SUBCOMPONENT_CANCEL_ID + '-footer',
                                className=(
                                    'atlanticus-manager__button '
                                    'atlanticus-manager__button--secondary'
                                ),
                            ),
                            html.Button(
                                'Guardar subcomponente',
                                id=SUBCOMPONENT_SAVE_ID,
                                className=(
                                    'atlanticus-manager__button atlanticus-manager__button--primary'
                                ),
                            ),
                        ],
                        className='ada-tools-admin__modal-actions',
                    ),
                ],
                className='ada-tools-admin__modal-dialog',
            ),
        ],
        id=SUBCOMPONENT_MODAL_ID,
        className='ada-tools-admin__modal',
    )


def _section_heading(title: str, description: str) -> object:
    return html.Div(
        [html.H3(title), html.P(description)],
        className='ada-tools-admin__section-heading-copy',
    )


def _field(label: str, control: object, help_text: str) -> object:
    return html.Label(
        [
            html.Span(label),
            control,
            html.Small(help_text, className='ada-tools-admin__field-help'),
        ],
        className='ada-tools-admin__field',
    )


def _reference_field(label: str, element_id: str, help_text: str) -> object:
    return html.Div(
        [
            html.Span(label),
            html.Code(id=element_id),
            html.Small(help_text, className='ada-tools-admin__field-help'),
        ],
        className='ada-tools-admin__field ada-tools-admin__field--reference',
    )
