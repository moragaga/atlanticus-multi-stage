from __future__ import annotations

import json
from pathlib import Path

PUBLICATIONS_ROOT = Path('/usr/app/.runtime/assets')
BASE_CSS_MARKER = '--atlanticus-web-font-family'
LOCAL_CSS_MARKER = '.smoke-application'
BASE_JS_MARKER = "dataset.atlanticusWeb='ready'"
LOCAL_JS_MARKER = "dataset.atlanticusWebBuildSmoke='ready'"


def main() -> None:
    publications = sorted(path for path in PUBLICATIONS_ROOT.iterdir() if path.is_dir())
    if len(publications) != 1:
        raise AssertionError(f'Expected one asset publication, found {len(publications)}')

    publication = publications[0]
    manifest = json.loads((publication / 'manifest.json').read_text(encoding='utf-8'))

    if manifest.get('optimized') is not True:
        raise AssertionError('Production asset publication is not optimized')
    if manifest.get('css_entries') != ['app.min.css']:
        raise AssertionError(f"Unexpected CSS entries: {manifest.get('css_entries')}")

    layer_names = [layer.get('name') for layer in manifest.get('layers', ())]
    if layer_names != ['atlanticus_web', 'smoke_application']:
        raise AssertionError(f'Unexpected asset layer order: {layer_names}')

    js_entries = manifest.get('js_entries')
    expected_js_entries = [
        '0010_atlanticus_web/js/0000__00_runtime.js',
        '0900_smoke_application/js/0000__900_application.js',
    ]
    if js_entries != expected_js_entries:
        raise AssertionError(f'Unexpected JavaScript entries: {js_entries}')

    css = (publication / 'app.min.css').read_text(encoding='utf-8')
    base_css_index = css.find(BASE_CSS_MARKER)
    local_css_index = css.find(LOCAL_CSS_MARKER)
    if base_css_index < 0 or local_css_index < 0 or base_css_index >= local_css_index:
        raise AssertionError('CSS wheel-to-local order was not preserved')
    if '\n    ' in css or '\n\n' in css:
        raise AssertionError('CSS bundle was not minified')

    base_js = (publication / expected_js_entries[0]).read_text(encoding='utf-8')
    local_js = (publication / expected_js_entries[1]).read_text(encoding='utf-8')
    if BASE_JS_MARKER not in base_js or LOCAL_JS_MARKER not in local_js:
        raise AssertionError('JavaScript minification output is unexpected')
    if '\n    ' in base_js or '\n    ' in local_js:
        raise AssertionError('JavaScript files were not minified')

    staged_css_sources = tuple(publication.rglob('css/*.css'))
    if staged_css_sources:
        raise AssertionError(f'Unminified staged CSS remains: {staged_css_sources}')

    source_css = Path('/usr/app/assets/css/900_override.css')
    source_js = Path('/usr/app/assets/js/900_application.js')
    if not source_css.is_file() or not source_js.is_file():
        raise AssertionError('Application source assets required for runtime publication are missing')

    print(f'Asset revision: {manifest["revision"]}')
    print(f'CSS entries: {manifest["css_entries"]}')
    print(f'JS entries: {js_entries}')
    print('Wheel -> local order: OK')
    print('CSS bundle minification: OK')
    print('JavaScript individual minification: OK')
    print('Source assets remain internal and are not part of the served snapshot: OK')


if __name__ == '__main__':
    main()
