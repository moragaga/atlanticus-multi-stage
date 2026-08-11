import atlanticus.web
import atlanticus.web.identity
import atlanticus.web.users

from atlanticus.web.application import create_web_application
from atlanticus.web.assets import AssetLayer
from atlanticus.web.identity.local import LocalIdentityProvider
from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.navigation import NavigationDefinition, NavigationMenu
from atlanticus.web.observability import WebObservability
from atlanticus.web.users.local import LocalUsersSource
from atlanticus.web.users.models import EffectiveUser


def test_web_namespace_composes_split_distributions() -> None:
    assert atlanticus.web.__spec__ is not None
    assert atlanticus.web.__spec__.submodule_search_locations is not None
    assert atlanticus.web.identity.__spec__ is not None
    assert atlanticus.web.identity.__spec__.submodule_search_locations is not None
    assert atlanticus.web.users.__spec__ is not None
    assert atlanticus.web.users.__spec__.submodule_search_locations is not None
    assert create_web_application is not None
    assert AuthenticatedIdentity is not None
    assert LocalIdentityProvider is not None
    assert AssetLayer is not None
    assert NavigationDefinition is not None
    assert NavigationMenu is not None
    assert EffectiveUser is not None
    assert LocalUsersSource is not None
    assert WebObservability is not None
