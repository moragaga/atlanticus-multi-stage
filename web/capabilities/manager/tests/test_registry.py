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
