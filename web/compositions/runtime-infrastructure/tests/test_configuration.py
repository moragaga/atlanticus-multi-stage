import pytest

from atlanticus.configuration import ConfigurationBootstrap, ConfigurationSource
from atlanticus.web.compositions.runtime_infrastructure import (
    SHAREPOINT_READ_ENDPOINT_VARIABLE,
    SHAREPOINT_ROOT_PATH_VARIABLE,
    SHAREPOINT_TOOL_PATH_VARIABLE,
    SHAREPOINT_WRITE_ENDPOINT_VARIABLE,
    create_sharepoint_configuration_specs,
    resolve_sharepoint_infrastructure_settings,
)


def test_sharepoint_specs_keep_signed_endpoints_sensitive() -> None:
    specs = create_sharepoint_configuration_specs()

    assert tuple(spec.key for spec in specs) == (
        SHAREPOINT_READ_ENDPOINT_VARIABLE,
        SHAREPOINT_WRITE_ENDPOINT_VARIABLE,
        SHAREPOINT_ROOT_PATH_VARIABLE,
        SHAREPOINT_TOOL_PATH_VARIABLE,
    )
    assert tuple(spec.key for spec in specs if spec.sensitive) == (
        SHAREPOINT_READ_ENDPOINT_VARIABLE,
        SHAREPOINT_WRITE_ENDPOINT_VARIABLE,
    )


def test_sharepoint_settings_split_transport_from_power_automate_semantics() -> None:
    specs = create_sharepoint_configuration_specs()
    configuration = _resolved_configuration(
        specs,
        {
            SHAREPOINT_READ_ENDPOINT_VARIABLE: (
                'https://power.example.com:443/read/invoke?api-version=1&sig=read-secret'
            ),
            SHAREPOINT_WRITE_ENDPOINT_VARIABLE: (
                'https://power.example.com:443/write/invoke?api-version=1&sig=write-secret'
            ),
            SHAREPOINT_ROOT_PATH_VARIABLE: 'conciencia_situacional',
            SHAREPOINT_TOOL_PATH_VARIABLE: 'operaciones_integradas',
        },
    )

    settings = resolve_sharepoint_infrastructure_settings(configuration)

    assert settings.http.base_url == 'https://power.example.com:443/'
    assert settings.gateway.read_endpoint == 'read/invoke'
    assert settings.gateway.write_endpoint == 'write/invoke'
    assert dict(settings.gateway.read_parameters) == {
        'api-version': '1',
        'sig': 'read-secret',
    }
    assert dict(settings.gateway.write_parameters) == {
        'api-version': '1',
        'sig': 'write-secret',
    }
    assert settings.paths.users_relative_path == 'conciencia_situacional/users'
    assert (
        settings.paths.navigation_relative_path
        == 'conciencia_situacional/operaciones_integradas/navigation'
    )
    assert settings.paths.tool_relative_path == 'conciencia_situacional/operaciones_integradas/tool'
    assert 'read-secret' not in repr(settings.gateway)
    assert 'write-secret' not in repr(settings.gateway)
    assert configuration.sources[SHAREPOINT_READ_ENDPOINT_VARIABLE] is ConfigurationSource.PROCESS


def test_sharepoint_endpoints_must_share_one_http_client_origin() -> None:
    specs = create_sharepoint_configuration_specs()
    configuration = _resolved_configuration(
        specs,
        {
            SHAREPOINT_READ_ENDPOINT_VARIABLE: 'https://read.example.com/invoke?sig=a',
            SHAREPOINT_WRITE_ENDPOINT_VARIABLE: 'https://write.example.com/invoke?sig=b',
            SHAREPOINT_ROOT_PATH_VARIABLE: 'root',
            SHAREPOINT_TOOL_PATH_VARIABLE: 'tool',
        },
    )

    with pytest.raises(
        ValueError,
        match='SharePoint Power Automate endpoints must share the same origin',
    ):
        resolve_sharepoint_infrastructure_settings(configuration)


def _resolved_configuration(specs, values):
    process_values = {'ENVIRONMENT': 'local', **values}
    bootstrap = ConfigurationBootstrap.from_process(specs=specs, process_values=process_values)
    return bootstrap.load(process_values=process_values)
