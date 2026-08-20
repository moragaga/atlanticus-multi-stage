from __future__ import annotations

from dataclasses import dataclass

from ada.compositions.web_bootstrap.models import AdaConfigurationBackends
from atlanticus.web.navigation.configuration import NavigationProjectionWorkflow
from atlanticus.web.users.configuration import UsersProjectionWorkflow


@dataclass(frozen=True, slots=True)
class AdaAccessProjectionSynchronizationResult:
    users_source_revision: str | None
    navigation_source_revision: str | None
    users_projected: bool
    navigation_projected: bool


def synchronize_ada_access_projections(
    *,
    configuration: AdaConfigurationBackends,
    actor: str = 'ada-bootstrap',
) -> AdaAccessProjectionSynchronizationResult:
    if not isinstance(configuration, AdaConfigurationBackends):
        raise TypeError('configuration must be AdaConfigurationBackends')
    normalized_actor = _require_actor(actor)

    users_workflow = UsersProjectionWorkflow(
        source=configuration.users_source,
        projection=configuration.users_projection,
        audit_actor_provider=lambda: normalized_actor,
    )
    users_status = users_workflow.get_status()
    users_revision = _optional_source_revision(users_status.source_revision, capability='Users')
    users_projected = (
        users_revision is not None and users_status.active_source_revision != users_revision
    )
    if users_projected:
        users_workflow.project(users_revision)

    navigation_workflow = NavigationProjectionWorkflow(
        source=configuration.navigation_source,
        projection=configuration.navigation_projection,
        audit_actor_provider=lambda: normalized_actor,
    )
    navigation_status = navigation_workflow.get_status()
    navigation_revision = _optional_source_revision(
        navigation_status.source_revision,
        capability='Navigation',
    )
    navigation_projected = (
        navigation_revision is not None
        and navigation_status.active_source_revision != navigation_revision
    )
    if navigation_projected:
        navigation_workflow.project(navigation_revision)

    return AdaAccessProjectionSynchronizationResult(
        users_source_revision=users_revision,
        navigation_source_revision=navigation_revision,
        users_projected=users_projected,
        navigation_projected=navigation_projected,
    )


def _require_actor(actor: str) -> str:
    if not isinstance(actor, str) or not actor.strip():
        raise TypeError('actor must be non-empty text')
    return actor.strip()


def _optional_source_revision(revision: str | None, *, capability: str) -> str | None:
    if revision is None:
        return None
    normalized = revision.strip()
    if not normalized:
        raise ValueError(f'{capability} SharePoint configuration revision must be non-empty')
    return normalized
