from pathlib import Path


def test_dashboard_page_keeps_root_route() -> None:
    source = (
        Path(__file__).resolve().parents[2] / 'src/integrated_operations/pages/dashboard.py'
    ).read_text(encoding='utf-8')

    assert "path='/'" in source
    assert 'build_integrated_operations_tool' in source
    assert '/integrated-operations' not in source
