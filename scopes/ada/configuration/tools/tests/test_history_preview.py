from ada.configuration.tools.web import build_tool_history_preview


def _text(value: object) -> str:
    if value is None:
        return ''
    if isinstance(value, (str, int, float)):
        return str(value)
    children = getattr(value, 'children', None)
    if isinstance(children, (list, tuple)):
        return ' '.join(_text(item) for item in children)
    return _text(children)


def test_tool_history_preview_shows_tool_structure_sources_and_links() -> None:
    preview = build_tool_history_preview(
        {
            'tool_key': 'process',
            'display_name': 'Proceso',
            'kind': 'process',
            'application_key': 'process',
            'operational_scope': 'plant',
            'sources': [{'key': 'pi', 'stale_after_seconds': 60}],
            'components': [
                {
                    'key': 'crusher',
                    'display_name': 'Chancado',
                    'scope': None,
                    'layout_role': 'center',
                    'subcomponents': [
                        {
                            'key': 'primary',
                            'display_name': 'Primario',
                            'linked_component_keys': [],
                        }
                    ],
                }
            ],
        }
    )

    text = _text(preview)

    assert 'Componentes 1' in text
    assert 'Subcomponentes 1' in text
    assert 'Fuentes 1' in text
    assert 'Proceso process' in text
    assert 'Tipo: process' in text
    assert 'pi Vencimiento: 60 s' in text
    assert 'Chancado crusher' in text
    assert 'Primario primary' in text
    assert 'Componentes vinculados: Sin vínculos' in text
