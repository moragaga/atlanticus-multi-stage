from ada.configuration.tools.models import ToolConfiguration, ToolConfigurationKind
from ada.configuration.tools.web.callbacks import (
    _browser_draft_matches_source,
    _structural_change_labels,
)
from ada.contracts.tool_manifest import ToolScope


def _integrated_source() -> ToolConfiguration:
    return ToolConfiguration(
        tool_key='integrated_operations',
        display_name='Operaciones Integradas',
        kind=ToolConfigurationKind.INTEGRATED_OPERATIONS,
    )


def _process_source() -> ToolConfiguration:
    return ToolConfiguration(
        tool_key='crushing',
        display_name='Chancado',
        kind=ToolConfigurationKind.PROCESS,
        operational_scope=ToolScope.MINE,
    )


def test_structural_change_labels_are_empty_without_a_published_source() -> None:
    assert (
        _structural_change_labels(
            source_configuration_data=None,
            tool_key='draft',
            kind_value='process',
            operational_scope='plant',
        )
        == ()
    )


def test_structural_change_labels_are_empty_when_editor_matches_source() -> None:
    source = _integrated_source()

    assert (
        _structural_change_labels(
            source_configuration_data=source.to_document(),
            tool_key=source.tool_key,
            kind_value=source.kind.value,
            operational_scope='global',
        )
        == ()
    )


def test_structural_change_labels_report_identity_type_and_area_changes() -> None:
    source = _integrated_source()

    assert _structural_change_labels(
        source_configuration_data=source.to_document(),
        tool_key='process_tool',
        kind_value='process',
        operational_scope='plant',
    ) == ('Identificador', 'Tipo / aplicación', 'Área')


def test_structural_change_labels_report_process_area_change() -> None:
    source = _process_source()

    assert _structural_change_labels(
        source_configuration_data=source.to_document(),
        tool_key=source.tool_key,
        kind_value=source.kind.value,
        operational_scope='plant',
    ) == ('Área',)


def test_source_baseline_is_only_taken_from_a_clean_source_backed_draft() -> None:
    clean = {
        'owner_subject_id': 'operator',
        'revision': 'source-revision',
        'base_source_revision': 'source-revision',
    }
    changed = {**clean, 'revision': 'draft-revision'}

    assert _browser_draft_matches_source(clean, 'operator') is True
    assert _browser_draft_matches_source(changed, 'operator') is False
    assert _browser_draft_matches_source(clean, 'another-operator') is False
