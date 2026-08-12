from __future__ import annotations

from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.users.cosmos.errors import UsersCosmosGatewayError
from atlanticus.web.users.cosmos.gateway import UsersCosmosGateway
from atlanticus.web.users.cosmos.keys import (
    email_lookup_key,
    identity_lookup_key,
    normalize_email,
    normalize_issuer,
    pending_user_id,
)
from atlanticus.web.users.cosmos.models import UserDocument, UserLookupDocument
from atlanticus.web.users.cosmos.profiles import UsersCosmosProfileCache
from atlanticus.web.users.errors import UsersIdentityConflictError, UsersSourceUnavailableError
from atlanticus.web.users.models import ResolvedUserRecord
from atlanticus.web.users.profiles import GUEST_PROFILE_KEY
from atlanticus.web.users.source import UsersSource


# Runtime source: identidad primero, email solo como reconciliación segura y guest persistente como último caso.
class UsersCosmosSource(UsersSource):
    def __init__(
        self,
        *,
        gateway: UsersCosmosGateway,
        profiles: UsersCosmosProfileCache,
    ) -> None:
        self._gateway = gateway
        self._profiles = profiles

    def resolve(self, identity: AuthenticatedIdentity) -> ResolvedUserRecord:
        self._profiles.ensure_current()
        try:
            return self._resolve(identity)
        except UsersCosmosGatewayError as error:
            raise UsersSourceUnavailableError('Users Cosmos source is unavailable') from error

    def _resolve(self, identity: AuthenticatedIdentity) -> ResolvedUserRecord:
        identity_key = identity_lookup_key(
            issuer=identity.issuer,
            subject_id=identity.subject_id,
        )
        identity_lookup = self._gateway.read_identity_lookup(identity_key)
        if identity_lookup is not None:
            return self._resolve_lookup_user(identity_lookup, identity=identity)

        if identity.email is not None:
            email_key = email_lookup_key(identity.email)
            email_lookup = self._gateway.read_email_lookup(email_key)
            if email_lookup is not None:
                return self._reconcile_email_user(
                    email_lookup,
                    identity_key=identity_key,
                    identity=identity,
                )

        return self._register_pending_guest(identity, identity_key=identity_key)

    def _resolve_lookup_user(
        self,
        lookup: UserLookupDocument,
        *,
        identity: AuthenticatedIdentity,
    ) -> ResolvedUserRecord:
        user = self._require_user(lookup.user_id)
        if user.issuer is not None and not _same_identity(user, identity):
            raise UsersIdentityConflictError('Identity lookup points to a different user identity')
        return _to_record(user, identity=identity)

    def _reconcile_email_user(
        self,
        lookup: UserLookupDocument,
        *,
        identity_key: str,
        identity: AuthenticatedIdentity,
    ) -> ResolvedUserRecord:
        user = self._require_user(lookup.user_id)
        if user.issuer is not None and not _same_identity(user, identity):
            raise UsersIdentityConflictError('Email belongs to a different authenticated identity')
        actual = self._gateway.create_lookup_if_absent(
            UserLookupDocument(
                kind='identity',
                lookup_key=identity_key,
                user_id=user.user_id,
            )
        )
        if actual.user_id != user.user_id:
            raise UsersIdentityConflictError(
                'Authenticated identity is already linked to another user'
            )
        return _to_record(user, identity=identity)

    # Las creaciones son idempotentes y usan claves deterministas; no se simula una transacción entre particiones.
    def _register_pending_guest(
        self,
        identity: AuthenticatedIdentity,
        *,
        identity_key: str,
    ) -> ResolvedUserRecord:
        user_id = pending_user_id(identity)
        display_name = identity.display_name or identity.email or 'Usuario pendiente'
        candidate = UserDocument(
            user_id=user_id,
            issuer=identity.issuer,
            subject_id=identity.subject_id,
            display_name=display_name,
            email=identity.email,
            profile_key=GUEST_PROFILE_KEY,
            enabled=True,
            pending=True,
            origin='identity',
        )
        user = self._gateway.create_user_if_absent(candidate)
        if not _same_pending_user(user, candidate):
            raise UsersIdentityConflictError(
                'Pending user id is already linked to another identity'
            )
        actual_identity = self._gateway.create_lookup_if_absent(
            UserLookupDocument(
                kind='identity',
                lookup_key=identity_key,
                user_id=user.user_id,
            )
        )
        if actual_identity.user_id != user.user_id:
            raise UsersIdentityConflictError(
                'Authenticated identity is already linked to another user'
            )
        if identity.email is not None:
            self._ensure_optional_email_lookup(identity.email, user.user_id)
        return _to_record(user, identity=identity)

    def _ensure_optional_email_lookup(self, email: str, user_id: str) -> None:
        actual = self._gateway.create_lookup_if_absent(
            UserLookupDocument(
                kind='email',
                lookup_key=email_lookup_key(email),
                user_id=user_id,
            )
        )
        if actual.user_id != user_id:
            return

    def _require_user(self, user_id: str) -> UserDocument:
        user = self._gateway.read_user(user_id)
        if user is None:
            raise UsersSourceUnavailableError('Users lookup points to a missing user')
        return user


# La comparación mantiene subject_id exacto y normaliza solo el issuer.
def _same_identity(user: UserDocument, identity: AuthenticatedIdentity) -> bool:
    if user.issuer is None or user.subject_id is None:
        return False
    return (
        normalize_issuer(user.issuer) == normalize_issuer(identity.issuer)
        and user.subject_id == identity.subject_id
    )


def _same_pending_user(current: UserDocument, candidate: UserDocument) -> bool:
    return (
        current.user_id == candidate.user_id
        and current.origin == 'identity'
        and current.pending
        and current.issuer is not None
        and candidate.issuer is not None
        and normalize_issuer(current.issuer) == normalize_issuer(candidate.issuer)
        and current.subject_id == candidate.subject_id
    )


def _to_record(user: UserDocument, *, identity: AuthenticatedIdentity) -> ResolvedUserRecord:
    email = user.email
    if email is None and identity.email is not None:
        email = normalize_email(identity.email)
    return ResolvedUserRecord(
        user_id=user.user_id,
        subject_id=identity.subject_id,
        display_name=user.display_name,
        email=email,
        enabled=user.enabled,
        pending=user.pending,
        profile_key=user.profile_key,
    )
