from pathlib import Path

from atlanticus_web_reference.application import build_definition


def test_reference_definition_uses_dynamic_pages_and_composable_web_module() -> None:
    definition = build_definition()
    module = definition.modules[0]

    assert definition.metadata.application_id == 'atlanticus-web-reference'
    assert module.page_packages == ('atlanticus_web_reference.pages',)
    assert module.register_services is not None
    assert module.register_health_checks is not None
    assert module.register_middlewares is not None
    assert module.register_routes is not None
    assert module.asset_layers[0].load_order == 900


def test_reference_entrypoints_live_inside_the_application_package() -> None:
    package = Path(__file__).parents[1] / 'src' / 'atlanticus_web_reference'

    assert (package / '__main__.py').is_file()
    assert (package / 'wsgi.py').is_file()
    assert (package / 'pages' / 'home.py').is_file()
    assert (package / 'pages' / 'status.py').is_file()
