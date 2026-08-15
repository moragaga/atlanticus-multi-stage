import pytest

from ada.contracts.tool_manifest import (
    ProcessBodySection,
    ToolManifest,
    ToolManifestError,
    ToolManifestLookupError,
    ToolManifestRegistry,
    ToolScope,
    ToolSection,
    ToolSectionKind,
    ToolSource,
    ToolSourceKey,
    ToolTarget,
)

_PI = ToolSource(ToolSourceKey.PI, stale_after_seconds=300)
_KPI = frozenset({ToolTarget.KPI})
_ALARM = frozenset({ToolTarget.ALARM})


def _region(key: str, scope: ToolScope = ToolScope.GLOBAL) -> ToolSection:
    return ToolSection(
        key=key,
        display_name=key,
        kind=ToolSectionKind.REGION,
        scope=scope,
    )


def test_source_requires_positive_integer_stale_threshold() -> None:
    with pytest.raises(ToolManifestError, match='must be greater than zero'):
        ToolSource(ToolSourceKey.PI, stale_after_seconds=0)

    with pytest.raises(ToolManifestError, match='must be an integer'):
        ToolSource(ToolSourceKey.PI, stale_after_seconds=True)


def test_manifest_requires_pi_and_unique_sources() -> None:
    section = _region('body')

    with pytest.raises(ToolManifestError, match='requires the pi source'):
        ToolManifest(
            'tool',
            'Tool',
            (ToolSource(ToolSourceKey.DISPATCH, stale_after_seconds=600),),
            (section,),
        )

    with pytest.raises(ToolManifestError, match='duplicate source keys'):
        ToolManifest('tool', 'Tool', (_PI, _PI), (section,))


def test_manifest_resolves_configured_sources() -> None:
    dispatch = ToolSource(ToolSourceKey.DISPATCH, stale_after_seconds=600)
    manifest = ToolManifest('tool', 'Tool', (_PI, dispatch), (_region('body'),))

    assert manifest.source(ToolSourceKey.PI) is _PI
    assert manifest.source(ToolSourceKey.DISPATCH) is dispatch
    assert manifest.has_source(ToolSourceKey.PI)


def test_subcomponent_identity_is_derived_from_component_and_subcomponent() -> None:
    section = ToolSection(
        component='flotacion',
        subcomponent='selectiva',
        display_name='Flotación Selectiva',
        kind=ToolSectionKind.SUBCOMPONENT,
        scope=ToolScope.PLANT,
        targets=_ALARM,
    )

    assert section.key == 'flotacion_selectiva'
    assert section.parent_key == 'flotacion'
    assert section.component == 'flotacion'
    assert section.subcomponent == 'selectiva'

    with pytest.raises(ToolManifestError, match='key is generated internally'):
        ToolSection(
            key='custom_key',
            component='flotacion',
            subcomponent='selectiva',
            display_name='Flotación Selectiva',
            kind=ToolSectionKind.SUBCOMPONENT,
            scope=ToolScope.PLANT,
        )

    with pytest.raises(ToolManifestError, match='parent_key is generated internally'):
        ToolSection(
            parent_key='flotacion',
            component='flotacion',
            subcomponent='selectiva',
            display_name='Flotación Selectiva',
            kind=ToolSectionKind.SUBCOMPONENT,
            scope=ToolScope.PLANT,
        )


def test_manifest_resolves_subcomponent_without_external_key_generation() -> None:
    body = _region('body', ToolScope.PLANT)
    component = ToolSection(
        key='flotacion',
        display_name='Flotación',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.PLANT,
        parent_key='body',
    )
    subcomponent = ToolSection(
        component='flotacion',
        subcomponent='selectiva',
        display_name='Flotación Selectiva',
        kind=ToolSectionKind.SUBCOMPONENT,
        scope=ToolScope.PLANT,
    )
    manifest = ToolManifest('tool', 'Tool', (_PI,), (body, component, subcomponent))

    assert manifest.subcomponent(component='flotacion', subcomponent='selectiva') is subcomponent


def test_manifest_rejects_duplicate_section_keys() -> None:
    section = _region('body')

    with pytest.raises(ToolManifestError, match='duplicate section keys'):
        ToolManifest('tool', 'Tool', (_PI,), (section, section))


def test_manifest_rejects_unknown_parent() -> None:
    section = ToolSection(
        key='center',
        display_name='Center',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.MINE,
        parent_key='body',
    )

    with pytest.raises(ToolManifestError, match='unknown parent'):
        ToolManifest('tool', 'Tool', (_PI,), (section,))


def test_manifest_rejects_scope_change_below_non_global_parent() -> None:
    body = _region('body', ToolScope.MINE)
    component = ToolSection(
        key='component',
        display_name='Component',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.PLANT,
        parent_key='body',
    )

    with pytest.raises(ToolManifestError, match='scope must match'):
        ToolManifest('tool', 'Tool', (_PI,), (body, component))


def test_manifest_rejects_invalid_kind_hierarchy() -> None:
    component = ToolSection(
        key='component',
        display_name='Component',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.GLOBAL,
    )
    child = ToolSection(
        key='child',
        display_name='Child',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.GLOBAL,
        parent_key='component',
    )

    with pytest.raises(ToolManifestError, match='Component can only be nested under a region'):
        ToolManifest('tool', 'Tool', (_PI,), (component, child))


def test_manifest_rejects_cycles() -> None:
    first = ToolSection(
        key='first',
        display_name='First',
        kind=ToolSectionKind.REGION,
        scope=ToolScope.GLOBAL,
        parent_key='second',
    )
    second = ToolSection(
        key='second',
        display_name='Second',
        kind=ToolSectionKind.REGION,
        scope=ToolScope.GLOBAL,
        parent_key='first',
    )

    with pytest.raises(ToolManifestError, match='contains a cycle'):
        ToolManifest('tool', 'Tool', (_PI,), (first, second))


def test_shared_subcomponent_is_resolved_from_each_linked_component() -> None:
    body = _region('body', ToolScope.MINE)
    carguio = ToolSection(
        key='carguio',
        display_name='Carguío',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.MINE,
        parent_key='body',
    )
    transporte = ToolSection(
        key='transporte',
        display_name='Transporte',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.MINE,
        parent_key='body',
    )
    shared = ToolSection(
        component='carguio',
        subcomponent='gestion_turno',
        display_name='Gestión Turno',
        kind=ToolSectionKind.SUBCOMPONENT,
        scope=ToolScope.MINE,
        linked_component_keys=('transporte',),
    )
    manifest = ToolManifest('tool', 'Tool', (_PI,), (body, carguio, transporte, shared))

    assert manifest.subcomponent(component='carguio', subcomponent='gestion_turno') is shared
    assert manifest.subcomponent(component='transporte', subcomponent='gestion_turno') is shared
    assert manifest.linked_components(shared.key) == (carguio, transporte)
    assert manifest.children('carguio') == (shared,)
    assert manifest.children('transporte') == ()


def test_manifest_rejects_invalid_shared_subcomponent_links() -> None:
    body = _region('body', ToolScope.MINE)
    linked_region = ToolSection(
        key='region',
        display_name='Region',
        kind=ToolSectionKind.REGION,
        scope=ToolScope.MINE,
        parent_key='body',
    )
    carguio = ToolSection(
        key='carguio',
        display_name='Carguío',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.MINE,
        parent_key='body',
    )

    with pytest.raises(ToolManifestError, match='can only link to a component'):
        ToolManifest(
            'tool',
            'Tool',
            (_PI,),
            (
                body,
                linked_region,
                carguio,
                ToolSection(
                    component='carguio',
                    subcomponent='shared',
                    display_name='Shared',
                    kind=ToolSectionKind.SUBCOMPONENT,
                    scope=ToolScope.MINE,
                    linked_component_keys=('region',),
                ),
            ),
        )

    with pytest.raises(ToolManifestError, match='unknown linked component'):
        ToolManifest(
            'tool',
            'Tool',
            (_PI,),
            (
                body,
                carguio,
                ToolSection(
                    component='carguio',
                    subcomponent='shared',
                    display_name='Shared',
                    kind=ToolSectionKind.SUBCOMPONENT,
                    scope=ToolScope.MINE,
                    linked_component_keys=('missing',),
                ),
            ),
        )


def test_manifest_rejects_shared_subcomponent_links_with_different_scope() -> None:
    body = _region('body')
    mine = ToolSection(
        key='mine_component',
        display_name='Mine',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.MINE,
        parent_key='body',
    )
    plant = ToolSection(
        key='plant_component',
        display_name='Plant',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.PLANT,
        parent_key='body',
    )
    shared = ToolSection(
        component='mine_component',
        subcomponent='shared',
        display_name='Shared',
        kind=ToolSectionKind.SUBCOMPONENT,
        scope=ToolScope.MINE,
        linked_component_keys=('plant_component',),
    )

    with pytest.raises(ToolManifestError, match='scope must match'):
        ToolManifest('tool', 'Tool', (_PI,), (body, mine, plant, shared))


def test_manifest_rejects_duplicate_shared_subcomponent_aliases() -> None:
    body = _region('body', ToolScope.MINE)
    first = ToolSection(
        key='first',
        display_name='First',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.MINE,
        parent_key='body',
    )
    second = ToolSection(
        key='second',
        display_name='Second',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.MINE,
        parent_key='body',
    )
    shared = ToolSection(
        component='first',
        subcomponent='shared',
        display_name='Shared',
        kind=ToolSectionKind.SUBCOMPONENT,
        scope=ToolScope.MINE,
        linked_component_keys=('second',),
    )
    duplicate = ToolSection(
        component='second',
        subcomponent='shared',
        display_name='Duplicate',
        kind=ToolSectionKind.SUBCOMPONENT,
        scope=ToolScope.MINE,
    )

    with pytest.raises(ToolManifestError, match='duplicate subcomponent identity'):
        ToolManifest('tool', 'Tool', (_PI,), (body, first, second, shared, duplicate))


def test_layout_role_is_only_valid_for_components_and_unique_in_manifest() -> None:
    with pytest.raises(ToolManifestError, match='Only components can declare a layout_role'):
        ToolSection(
            key='region',
            display_name='Region',
            kind=ToolSectionKind.REGION,
            scope=ToolScope.PLANT,
            layout_role=ProcessBodySection.CENTER,
        )

    first = ToolSection(
        key='first',
        display_name='First',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.PLANT,
        layout_role=ProcessBodySection.CENTER,
    )
    second = ToolSection(
        key='second',
        display_name='Second',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.PLANT,
        layout_role=ProcessBodySection.CENTER,
    )

    with pytest.raises(ToolManifestError, match='duplicate layout roles'):
        ToolManifest('tool', 'Tool', (_PI,), (first, second))


def test_manifest_resolves_component_by_layout_role() -> None:
    center = ToolSection(
        key='planta_molibdeno',
        display_name='Planta Molibdeno',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.PLANT,
        layout_role=ProcessBodySection.CENTER,
        targets=_KPI,
    )
    manifest = ToolManifest('tool', 'Tool', (_PI,), (center,))

    assert manifest.component_for_layout_role(ProcessBodySection.CENTER) is center

    with pytest.raises(ToolManifestLookupError, match='Unknown layout role'):
        manifest.component_for_layout_role(ProcessBodySection.LEFT)


def test_require_target_rejects_non_targetable_section() -> None:
    manifest = ToolManifest('tool', 'Tool', (_PI,), (_region('body'),))

    with pytest.raises(ToolManifestLookupError, match='does not accept target'):
        manifest.require_target('body', ToolTarget.KPI)


def test_registry_requires_unique_tools_and_resolves_targets() -> None:
    manifest = ToolManifest(
        'tool',
        'Tool',
        (_PI,),
        (
            ToolSection(
                key='center',
                display_name='Center',
                kind=ToolSectionKind.COMPONENT,
                scope=ToolScope.MINE,
                targets=_KPI,
            ),
        ),
    )
    registry = ToolManifestRegistry((manifest,))

    assert registry.require('tool') is manifest
    assert registry.sections_for_target('tool', ToolTarget.KPI) == manifest.sections

    with pytest.raises(ToolManifestError, match='duplicate tool keys'):
        ToolManifestRegistry((manifest, manifest))
