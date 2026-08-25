from datetime import UTC, datetime, timedelta

import pytest

from ada.runtime.delivery_collector import (
    RuntimeDeliveryCollectorError,
    build_acquired_refresh_lock,
    build_refresh_signal,
    build_released_refresh_lock,
    is_refresh_lock_expired,
)


def test_refresh_signal_and_lock_preserve_one_active_token() -> None:
    now = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)
    signal = build_refresh_signal(now=now)

    lock = build_acquired_refresh_lock(signal, now=now)

    assert lock['is_running'] is True
    assert lock['active_token'] == signal['token']
    assert lock['started_at_utc'] == '2026-08-25T12:00:00Z'


def test_active_refresh_lock_expires_after_ttl() -> None:
    started = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)
    lock = build_acquired_refresh_lock(build_refresh_signal(now=started), now=started)

    assert not is_refresh_lock_expired(lock, ttl_seconds=90, now=started + timedelta(seconds=90))
    assert is_refresh_lock_expired(lock, ttl_seconds=90, now=started + timedelta(seconds=91))


def test_released_lock_is_never_considered_expired() -> None:
    lock = build_released_refresh_lock(now=datetime(2026, 8, 25, 12, 0, tzinfo=UTC))

    assert lock['is_running'] is False
    assert not is_refresh_lock_expired(lock)


def test_refresh_lock_rejects_invalid_ttl() -> None:
    with pytest.raises(RuntimeDeliveryCollectorError, match='greater than zero'):
        is_refresh_lock_expired({'is_running': True}, ttl_seconds=0)
