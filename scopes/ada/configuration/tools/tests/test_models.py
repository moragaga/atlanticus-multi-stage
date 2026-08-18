from dataclasses import replace

import pytest

from ada.configuration.tools import (
    ToolComponentConfiguration,
    ToolConfiguration,
    ToolConfigurationCatalog,
    ToolConfigurationKind,
    ToolSourceConfiguration,
    ToolSubcomponentConfiguration,
    build_identity_key,
)
from ada.configuration.tools.errors import ToolConfigurationValidationError
from ada.contracts.tool_manifest import ToolScope, ToolSourceKey


def test_identity_is_generated_from_display_name_but_is_not_recomputed_on_rename() -> None:
    key = build_identity_key('Transporte de Fluidos')
    original = ToolConfiguration(
        tool_key=key,
        display_name='Transporte de Fluidos',
        kind=ToolConfigurationKind.PROCESS,
    )

    renamed = replace(original, display_name='Transporte de Fluidos Planta')

    assert key == 'transporte_de_fluidos'
    assert renamed.tool_key == 'transporte_de_fluidos'


def test_catalog_roundtrip_preserves_order_and_stable_ids() -> None:
    catalog = ToolConfigurationCatalog(
        (
            ToolConfiguration(
                tool_key='integrated_operations',
                display_name='Operaciones Integradas',
                kind=ToolConfigurationKind.INTEGRATED_OPERATIONS,
                sources=(ToolSourceConfiguration(ToolSourceKey.PI, 300),),
                components=(
                    ToolComponentConfiguration(
                        key='flotacion',
                        display_name='Flotación',
                        scope=ToolScope.PLANT,
                        subcomponents=(
                            ToolSubcomponentConfiguration(
                                key='colectiva',
                                display_name='Colectiva',
                            ),
                            ToolSubcomponentConfiguration(
                                key='selectiva',
                                display_name='Selectiva',
                            ),
                        ),
                    ),
                ),
            ),
        )
    )

    restored = ToolConfigurationCatalog.from_document(catalog.to_document())

    assert restored == catalog


def test_source_document_rejects_boolean_freshness() -> None:
    with pytest.raises(ToolConfigurationValidationError, match='contract is invalid'):
        ToolSourceConfiguration.from_document(
            {'key': 'pi', 'stale_after_seconds': True}
        )
