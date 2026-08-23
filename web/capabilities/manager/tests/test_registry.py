import pytest

from atlanticus.web.manager import (
    DefaultManagerAuthorizationPolicy,
    ManagerDefinitionError,
    ManagerModule,
    ManagerModuleGroup,
    ManagerModuleRegistry,
    ManagerPrincipal,
)


def _layout(_services):
    return None


def test_registry_orders_groups_and_modules_without_owning_domain_configuration() -> None:
    registry = ManagerModuleRegistry(
        groups=(ManagerModuleGroup('configuration', 'Configuraciones', 10),),
        modules=(
            ManagerModule(
                key='kpis',
                group_key='configuration',
                title='KPIs',
                route='/kpis',
                order=20,
                layout=_layout,
                workflow_service='kpis.workflow',
            ),
            ManagerModule(
                key='tools',
                group_key='configuration',
                title='Herramientas',
                route='/tools',
                order=10,
                layout=_layout,
                workflow_service='tools.workflow',
            ),
        ),
    )

    assert [module.key for module in registry.modules] == ['tools', 'kpis']
    assert registry.find_by_route('/tools').key == 'tools'


def test_registry_rejects_duplicate_routes() -> None:
    with pytest.raises(ManagerDefinitionError, match='route is duplicated'):
        ManagerModuleRegistry(
            groups=(ManagerModuleGroup('configuration', 'Configuraciones', 10),),
            modules=(
                ManagerModule(
                    key='tools',
                    group_key='configuration',
                    title='Herramientas',
                    route='/tools',
                    order=10,
                    layout=_layout,
                    workflow_service='tools.workflow',
                ),
                ManagerModule(
                    key='kpis',
                    group_key='configuration',
                    title='KPIs',
                    route='/tools',
                    order=20,
                    layout=_layout,
                    workflow_service='kpis.workflow',
                ),
            ),
        )


def test_default_authorization_allows_local_administrator() -> None:
    principal = ManagerPrincipal(
        subject_id='local',
        display_name='Administrador local',
        is_local=True,
    )
    module = ManagerModule(
        key='tools',
        group_key='configuration',
        title='Herramientas',
        route='/tools',
        order=10,
        layout=_layout,
        workflow_service='tools.workflow',
    )

    assert DefaultManagerAuthorizationPolicy().can_view(principal, module)


def test_registry_applies_host_route_prefix_without_changing_module_route() -> None:
    module = ManagerModule(
        key='tools',
        group_key='configuration',
        title='Herramientas',
        route='/tools',
        order=10,
        layout=_layout,
        workflow_service='tools.workflow',
    )
    registry = ManagerModuleRegistry(
        groups=(ManagerModuleGroup('configuration', 'Configuraciones', 10),),
        modules=(module,),
        route_prefix='/manager',
    )

    assert module.route == '/tools'
    assert registry.root_route == '/manager'
    assert registry.route_for(module) == '/manager/tools'
    assert registry.find_by_route('/manager/tools') is module
    assert registry.find_by_route('/tools') is None


def test_registry_rejects_invalid_route_prefix() -> None:
    with pytest.raises(ManagerDefinitionError, match='route prefix'):
        ManagerModuleRegistry(
            groups=(ManagerModuleGroup('configuration', 'Configuraciones', 10),),
            modules=(
                ManagerModule(
                    key='tools',
                    group_key='configuration',
                    title='Herramientas',
                    route='/tools',
                    order=10,
                    layout=_layout,
                    workflow_service='tools.workflow',
                ),
            ),
            route_prefix='/manager/',
        )


def test_registry_rejects_non_callable_history_preview_renderer() -> None:
    with pytest.raises(ManagerDefinitionError, match='history preview renderer'):
        ManagerModuleRegistry(
            groups=(ManagerModuleGroup('configuration', 'Configuraciones', 10),),
            modules=(
                ManagerModule(
                    key='tools',
                    group_key='configuration',
                    title='Herramientas',
                    route='/tools',
                    order=10,
                    layout=_layout,
                    workflow_service='tools.workflow',
                    history_preview_renderer='invalid',
                ),
            ),
        )


def test_registry_accepts_complete_optional_workspace_import_definition() -> None:
    module = ManagerModule(
        key='tools',
        group_key='configuration',
        title='Herramientas',
        route='/tools',
        order=10,
        layout=_layout,
        workflow_service='tools.workflow',
        workspace_import_service='tools.import',
        workspace_import_name='Archivo local',
    )

    registry = ManagerModuleRegistry(
        groups=(ManagerModuleGroup('configuration', 'Configuraciones', 10),),
        modules=(module,),
    )

    assert registry.require('tools').workspace_import_service == 'tools.import'
    assert registry.require('tools').workspace_import_name == 'Archivo local'


@pytest.mark.parametrize(
    ('service', 'name'),
    ((None, 'Archivo local'), ('tools.import', None), ('', 'Archivo local'), ('tools.import', '')),
)
def test_registry_rejects_partial_or_empty_workspace_import_definition(
    service: str | None,
    name: str | None,
) -> None:
    with pytest.raises(ManagerDefinitionError, match='workspace import'):
        ManagerModuleRegistry(
            groups=(ManagerModuleGroup('configuration', 'Configuraciones', 10),),
            modules=(
                ManagerModule(
                    key='tools',
                    group_key='configuration',
                    title='Herramientas',
                    route='/tools',
                    order=10,
                    layout=_layout,
                    workflow_service='tools.workflow',
                    workspace_import_service=service,
                    workspace_import_name=name,
                ),
            ),
        )
