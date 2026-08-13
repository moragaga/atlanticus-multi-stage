from pathlib import Path


def test_time_status_assets_keep_slots_stable_and_use_rem_geometry() -> None:
    resources = (
        Path(__file__).parents[1] / 'src' / 'ada' / 'ui' / 'shell' / 'time_status' / 'resources'
    )
    css = (resources / 'css' / '10-time-status.css').read_text(encoding='utf-8')
    js = (resources / 'js' / '10-time-status.js').read_text(encoding='utf-8')

    assert 'data-time-status-source' in js
    assert 'data-stale-after-seconds' not in js
    assert 'source.dataset.staleAfterSeconds' in js
    assert 'window.AppTicker.subscribe(update)' in js
    assert 'hace menos de 10 segundos' in js
    assert 'America/Santiago' in js
    assert 'setInterval' not in js
    assert 'padding: .2rem .65rem;' in css
    assert 'border-bottom: 1px solid' in css
    assert 'overflow-x: hidden' not in css
