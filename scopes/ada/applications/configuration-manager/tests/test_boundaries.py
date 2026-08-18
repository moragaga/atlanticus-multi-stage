from pathlib import Path


def test_application_composition_does_not_own_sharepoint_or_cosmos_contracts() -> None:
    root = Path(__file__).parents[1] / 'src/ada/applications/configuration_manager'
    product = '\n'.join(path.read_text(encoding='utf-8') for path in root.glob('*.py'))

    assert 'SharePoint' not in product
    assert 'Cosmos' not in product
