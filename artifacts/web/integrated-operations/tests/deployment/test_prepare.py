import integrated_operations.deployment.prepare as prepare


def test_prepare_uses_safe_product_default(monkeypatch) -> None:
    captured = {}
    monkeypatch.setattr(
        prepare,
        'prepare_ada_web_deployment',
        lambda **kwargs: captured.update(kwargs),
    )

    prepare.main([])

    assert captured['create_databases_if_missing'] is False
    assert captured['actor'] == 'ada-bootstrap'


def test_prepare_can_explicitly_create_database(monkeypatch) -> None:
    captured = {}
    monkeypatch.setattr(
        prepare,
        'prepare_ada_web_deployment',
        lambda **kwargs: captured.update(kwargs),
    )

    prepare.main(['--create-database-if-missing', '--actor', 'local-bootstrap'])

    assert captured['create_databases_if_missing'] is True
    assert captured['actor'] == 'local-bootstrap'
