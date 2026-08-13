import pytest

from ada.contracts.tool_manifest import (
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


def test_source_requires_positive_integer_stale_threshold() -> None:
    with pytest.raises(ToolManifestError, match='must be greater than zero'):
        ToolSource(ToolSourceKey.PI, stale_after_seconds=0)

    with pytest.raises(ToolManifestError, match='must be an integer'):
        ToolSource(ToolSourceKey.PI, stale_after_seconds=True)


def test_manifest_requires_pi_and_unique_sources() -> None:
    section = ToolSection('body', 'Body', ToolSectionKind.REGION, ToolScope.GLOBAL)

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
    manifest = ToolManifest(
        'tool',
        'Tool',
        (_PI, dispatch),
        (ToolSection('body', 'Body', ToolSectionKind.REGION, ToolScope.GLOBAL),),
    )

    assert manifest.source(ToolSourceKey.PI) is _PI
    assert manifest.source(ToolSourceKey.DISPATCH) is dispatch
    assert manifest.has_source(ToolSourceKey.PI)


def test_manifest_rejects_duplicate_section_keys() -> None:
    section = ToolSection('body', 'Body', ToolSectionKind.REGION, ToolScope.GLOBAL)

    with pytest.raises(ToolManifestError, match='duplicate section keys'):
        ToolManifest('tool', 'Tool', (_PI,), (section, section))


def test_manifest_rejects_unknown_parent() -> None:
    section = ToolSection(
        'center',
        'Center',
        ToolSectionKind.COMPONENT,
        ToolScope.MINE,
        parent_key='body',
    )

    with pytest.raises(ToolManifestError, match='unknown parent'):
        ToolManifest('tool', 'Tool', (_PI,), (section,))


def test_manifest_rejects_scope_change_below_non_global_parent() -> None:
    body = ToolSection('body', 'Body', ToolSectionKind.REGION, ToolScope.MINE)
    component = ToolSection(
        'component',
        'Component',
        ToolSectionKind.COMPONENT,
        ToolScope.PLANT,
        parent_key='body',
    )

    with pytest.raises(ToolManifestError, match='scope must match'):
        ToolManifest('tool', 'Tool', (_PI,), (body, component))


def test_manifest_rejects_invalid_kind_hierarchy() -> None:
    component = ToolSection(
        'component',
        'Component',
        ToolSectionKind.COMPONENT,
        ToolScope.GLOBAL,
    )
    child = ToolSection(
        'child',
        'Child',
        ToolSectionKind.COMPONENT,
        ToolScope.GLOBAL,
        parent_key='component',
    )

    with pytest.raises(ToolManifestError, match='Component can only be nested under a region'):
        ToolManifest('tool', 'Tool', (_PI,), (component, child))


def test_manifest_rejects_cycles() -> None:
    first = ToolSection(
        'first',
        'First',
        ToolSectionKind.REGION,
        ToolScope.GLOBAL,
        parent_key='second',
    )
    second = ToolSection(
        'second',
        'Second',
        ToolSectionKind.REGION,
        ToolScope.GLOBAL,
        parent_key='first',
    )

    with pytest.raises(ToolManifestError, match='contains a cycle'):
        ToolManifest('tool', 'Tool', (_PI,), (first, second))


def test_require_target_rejects_non_targetable_section() -> None:
    manifest = ToolManifest(
        'tool',
        'Tool',
        (_PI,),
        (ToolSection('body', 'Body', ToolSectionKind.REGION, ToolScope.GLOBAL),),
    )

    with pytest.raises(ToolManifestLookupError, match='does not accept target'):
        manifest.require_target('body', ToolTarget.KPI)


def test_registry_requires_unique_tools_and_resolves_targets() -> None:
    manifest = ToolManifest(
        'tool',
        'Tool',
        (_PI,),
        (
            ToolSection(
                'center',
                'Center',
                ToolSectionKind.COMPONENT,
                ToolScope.MINE,
                targets=frozenset({ToolTarget.KPI}),
            ),
        ),
    )
    registry = ToolManifestRegistry((manifest,))

    assert registry.require('tool') is manifest
    assert registry.sections_for_target('tool', ToolTarget.KPI) == manifest.sections

    with pytest.raises(ToolManifestError, match='duplicate tool keys'):
        ToolManifestRegistry((manifest, manifest))
