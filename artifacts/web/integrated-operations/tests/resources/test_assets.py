from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_application_css_is_filename_ordered_without_list_manifest() -> None:
    css = ROOT / 'src/integrated_operations/resources/css'
    files = sorted(item.name for item in css.iterdir() if item.is_file())

    assert files == ['10-integrated-operations.css']
    assert not (css / 'css.list').exists()


def test_source_assets_live_in_resources_not_dash_assets() -> None:
    package = ROOT / 'src/integrated_operations'

    assert (package / 'resources/css/10-integrated-operations.css').is_file()
    assert not (package / 'assets').exists()


def test_real_header_places_latest_inside_the_three_slot_vertical_stack() -> None:
    css = (ROOT / 'src/integrated_operations/resources/css/10-integrated-operations.css').read_text(
        encoding='utf-8'
    )

    assert '.integrated-operations .global-indicator__content' in css
    assert 'flex-direction: column;' in css
    assert ".global-indicator[data-has-last-measurement='true']" in css
    assert '.global-indicator__row--empty' in css
    assert '.integrated-operations .global-indicator__last-measurement' in css
    assert 'border-left: 0;' in css
    assert '.integrated-operations .global-indicator__last-measurement--empty' in css
    assert 'display: none;' in css
