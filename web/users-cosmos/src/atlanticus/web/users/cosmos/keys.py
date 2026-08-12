from __future__ import annotations

import hashlib

from atlanticus.web.identity.models import AuthenticatedIdentity

_LOOKUP_VERSION = 'v1'


def normalize_issuer(value: str) -> str:
    return value.strip().casefold()


def normalize_email(value: str) -> str:
    return value.strip().casefold()


def identity_lookup_key(*, issuer: str, subject_id: str) -> str:
    material = f'{_LOOKUP_VERSION}\x1f{normalize_issuer(issuer)}\x1f{subject_id.strip()}'
    return f'identity:{hashlib.sha256(material.encode()).hexdigest()}'


def email_lookup_key(email: str) -> str:
    material = f'{_LOOKUP_VERSION}\x1f{normalize_email(email)}'
    return f'email:{hashlib.sha256(material.encode()).hexdigest()}'


def pending_user_id(identity: AuthenticatedIdentity) -> str:
    lookup_key = identity_lookup_key(issuer=identity.issuer, subject_id=identity.subject_id)
    digest = lookup_key.removeprefix('identity:')[:24]
    return f'pending:{digest}'


def user_partition_key(user_id: str) -> str:
    return f'user:{user_id.strip()}'
