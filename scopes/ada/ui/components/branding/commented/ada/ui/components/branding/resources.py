"""Acceso seguro a los assets empaquetados por la componente de branding."""

from importlib.resources import files
from pathlib import PurePosixPath

from .errors import BrandDefinitionError

_RESOURCE_ROOT = 'resources/img'


def brand_asset_resource(resource_name: str):
    _validate_resource_name(resource_name)
    return files('ada.ui.components.branding').joinpath(_RESOURCE_ROOT, resource_name)


def brand_asset_package_path(resource_name: str) -> str:
    _validate_resource_name(resource_name)
    return PurePosixPath(_RESOURCE_ROOT, resource_name).as_posix()


def _validate_resource_name(resource_name: str) -> None:
    path = PurePosixPath(resource_name)
    if len(path.parts) != 1 or resource_name in {'', '.', '..'}:
        raise BrandDefinitionError('Brand asset resource must be a file name')
