import ast
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ada.configuration.tools import (
    ToolConfigurationProjection,
    build_component_runtime_binding,
    build_subcomponent_runtime_binding,
    build_tool_runtime_bindings,
)
from ada.configuration.tools.errors import ToolConfigurationProjectionError
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST


def test_component_runtime_ids_are_deterministic_from_stable_component_key() -> None:
    binding = build_component_runtime_binding('molienda')

    assert binding.component_key == 'molienda'
    assert binding.wrapper_id == 'ada-runtime-component-molienda'
    assert binding.kpi_latest_store_id == 'ada-runtime-kpi-latest-molienda'
    assert binding.kpi_timeseries_store_id == 'ada-runtime-kpi-timeseries-molienda'


def test_subcomponent_runtime_wrapper_is_deterministic_and_shared_alias_resolves_same_binding() -> (
    None
):
    bindings = build_tool_runtime_bindings(INTEGRATED_OPERATIONS_MANIFEST)

    direct = bindings.subcomponent(
        component_key='carguio',
        subcomponent_key='gestion_carguio_turno',
    )
    linked = bindings.subcomponent(
        component_key='transporte',
        subcomponent_key='gestion_carguio_turno',
    )

    assert direct is linked
    assert direct.wrapper_id == ('ada-runtime-subcomponent-carguio-gestion_carguio_turno')
    assert direct.linked_component_keys == ('transporte',)


def test_runtime_bindings_include_every_manifest_component_with_kpi_stores() -> None:
    bindings = build_tool_runtime_bindings(INTEGRATED_OPERATIONS_MANIFEST)
    manifest_components = tuple(
        section.key
        for section in INTEGRATED_OPERATIONS_MANIFEST.sections
        if section.kind.value == 'component'
    )

    assert tuple(binding.component_key for binding in bindings.components) == manifest_components
    assert all(binding.kpi_latest_store_id for binding in bindings.components)
    assert all(binding.kpi_timeseries_store_id for binding in bindings.components)


def test_projection_schema_three_embeds_runtime_bindings_derived_from_manifest() -> None:
    projection = ToolConfigurationProjection.create(
        source_revision='source-revision',
        projected_by='tester',
        projected_at_utc=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
    )

    document = projection.to_document(item_id='tool', partition_key='tool')

    assert document['schema_version'] == 3
    assert document['runtime'] == projection.runtime.to_document()
    assert projection.runtime.component('molienda').wrapper_id == 'ada-runtime-component-molienda'


def test_projection_schema_two_is_read_compatibly_and_derives_runtime_bindings() -> None:
    projection = ToolConfigurationProjection.create(
        source_revision='source-revision',
        projected_by='tester',
        projected_at_utc=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
    )
    document = projection.to_document(item_id='tool', partition_key='tool')
    document['schema_version'] = 2
    document.pop('runtime')

    restored = ToolConfigurationProjection.from_document(document)

    assert restored == projection
    assert restored.to_document(item_id='tool', partition_key='tool')['schema_version'] == 3


def test_projection_rejects_runtime_binding_that_does_not_match_manifest() -> None:
    projection = ToolConfigurationProjection.create(
        source_revision='source-revision',
        projected_by='tester',
        projected_at_utc=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
    )
    document = projection.to_document(item_id='tool', partition_key='tool')
    runtime = document['runtime']
    assert isinstance(runtime, dict)
    components = runtime['components']
    assert isinstance(components, list)
    first = components[0]
    assert isinstance(first, dict)
    first['wrapper_id'] = 'wrong-wrapper'

    with pytest.raises(ToolConfigurationProjectionError, match='binding is invalid'):
        ToolConfigurationProjection.from_document(document)


def test_runtime_binding_builders_reject_invalid_identity_keys() -> None:
    with pytest.raises(ToolConfigurationProjectionError, match='invalid format'):
        build_component_runtime_binding('Molienda con espacios')

    with pytest.raises(ToolConfigurationProjectionError, match='invalid format'):
        build_subcomponent_runtime_binding(
            component_key='molienda',
            subcomponent_key='Subcomponente Inválido',
        )


def test_runtime_binding_commented_mirrors_match_productive_ast() -> None:
    package = Path(__file__).parents[1]
    pairs = (
        ('src/ada/configuration/tools/runtime.py', 'commented/ada/configuration/tools/runtime.py'),
        (
            'src/ada/configuration/tools/projection.py',
            'commented/ada/configuration/tools/projection.py',
        ),
        (
            'src/ada/configuration/tools/__init__.py',
            'commented/ada/configuration/tools/__init__.py',
        ),
        (
            'src/ada/configuration/tools/web/callbacks.py',
            'commented/ada/configuration/tools/web/callbacks.py',
        ),
    )

    for productive_name, commented_name in pairs:
        productive = ast.dump(
            ast.parse(package.joinpath(productive_name).read_text(encoding='utf-8')),
            include_attributes=False,
        )
        commented = ast.dump(
            ast.parse(package.joinpath(commented_name).read_text(encoding='utf-8')),
            include_attributes=False,
        )
        assert commented == productive, productive_name
