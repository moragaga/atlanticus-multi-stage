import tomllib
from importlib.resources import files
from pathlib import Path


def test_reference_assets_are_gallery_only() -> None:
    resources = files('ada.applications.reference').joinpath('resources')
    css = resources.joinpath('css')
    css_list = css.joinpath('css.list').read_text().splitlines()

    assert css_list == ['00-reference.css']
    assert css.joinpath(css_list[0]).is_file()
    assert not resources.joinpath('js').is_dir()

    stylesheet = css.joinpath(css_list[0]).read_text()
    assert 'data-ada-io-view' not in stylesheet
    assert 'ada-io-view' not in stylesheet
    assert '.ada-integrated-operations-tool' not in stylesheet
    assert '.reference-ada__header' not in stylesheet


def test_reference_depends_only_on_transversal_ada_composition() -> None:
    pyproject_path = Path(__file__).parents[1] / 'pyproject.toml'
    pyproject = tomllib.loads(pyproject_path.read_text())
    dependencies = pyproject['project']['dependencies']

    composition_dependencies = [
        dependency for dependency in dependencies if dependency.startswith('ada-composition-')
    ]

    assert composition_dependencies == ['ada-composition-web-application==0.1.0']
