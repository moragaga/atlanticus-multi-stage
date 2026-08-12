import pytest

from ada.contracts.tool_manifest import (
    ToolManifest,
    ToolManifestError,
    ToolManifestLookupError,
    ToolManifestRegistry,
    ToolScope,
    ToolSection,
    ToolSectionKind,
    ToolTarget,
)


def test_manifest_rejects_duplicate_section_keys() -> None:
    section = ToolSection('body', 'Body', ToolSectionKind.REGION, ToolScope.GLOBAL)

    with pytest.raises(ToolManifestError, match='duplicate section keys'):
        ToolManifest('tool', 'Tool', (section, section))


def test_manifest_rejects_unknown_parent() -> None:
    section = ToolSection(
        'center',
        'Center',
        ToolSectionKind.COMPONENT,
        ToolScope.MINE,
        parent_key='body',
    )

    with pytest.raises(ToolManifestError, match='unknown parent'):
        ToolManifest('tool', 'Tool', (section,))


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
        ToolManifest('tool', 'Tool', (body, component))


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
        ToolManifest('tool', 'Tool', (component, child))


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
        ToolManifest('tool', 'Tool', (first, second))


def test_require_target_rejects_non_targetable_section() -> None:
    manifest = ToolManifest(
        'tool',
        'Tool',
        (ToolSection('body', 'Body', ToolSectionKind.REGION, ToolScope.GLOBAL),),
    )

    with pytest.raises(ToolManifestLookupError, match='does not accept target'):
        manifest.require_target('body', ToolTarget.KPI)


def test_registry_requires_unique_tools_and_resolves_targets() -> None:
    manifest = ToolManifest(
        'tool',
        'Tool',
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
