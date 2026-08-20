from unittest.mock import Mock

import pytest

from integrated_operations.application.wsgi import WorkerApplication


def test_worker_application_import_does_not_open_runtime() -> None:
    factory = Mock()

    WorkerApplication(factory)

    factory.assert_not_called()


def test_worker_application_warmup_opens_runtime_before_requests() -> None:
    runtime = Mock()
    runtime.server.return_value = ['response']
    factory = Mock(return_value=runtime)
    application = WorkerApplication(factory)

    application.warmup()
    response = application({}, Mock())

    assert response == ['response']
    factory.assert_called_once_with()
    runtime.server.assert_called_once()


def test_worker_application_reuses_runtime_within_process() -> None:
    runtime = Mock()
    runtime.server.return_value = ['response']
    factory = Mock(return_value=runtime)
    application = WorkerApplication(factory)

    application.warmup()
    application.warmup()
    application({}, Mock())
    application({}, Mock())

    factory.assert_called_once_with()
    assert runtime.server.call_count == 2


def test_worker_application_rejects_request_before_worker_warmup() -> None:
    application = WorkerApplication(Mock())

    with pytest.raises(RuntimeError, match='worker runtime is not initialized'):
        application({}, Mock())


def test_worker_application_close_releases_runtime() -> None:
    runtime = Mock()
    application = WorkerApplication(Mock(return_value=runtime))
    application.warmup()

    application.close()
    application.close()

    runtime.close.assert_called_once_with()
