import pytest

from pyjudo import ServiceContainer, ServiceLife
from pyjudo.exceptions import ServiceResolutionError


def test_scoped_lifetime(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA, ServiceLife.SCOPED)

    with container.create_scope() as scope:
        instance1 = scope.get(services.IServiceA)
        instance2 = scope.get(services.IServiceA)

        assert instance1 is instance2
        assert instance1.value == "A"


def test_scoped_lifetime_multiple_scopes(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA, ServiceLife.SCOPED)

    with container.create_scope() as scope1:
        instance1 = scope1.get(services.IServiceA)

        with container.create_scope() as scope2:
            instance2 = scope2.get(services.IServiceA)

            assert instance1 is not instance2
            assert instance1.value == "A"
            assert instance2.value == "A"


def test_scoped_with_no_scope(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA, ServiceLife.SCOPED)

    with pytest.raises(ServiceResolutionError):
        _ = container.get(services.IServiceA)


def test_scoped_with_disposable(services):
    container = ServiceContainer()
    _ = container.register(
        services.IServiceA, services.SoftDisposableService, ServiceLife.SCOPED
    )

    with container.create_scope() as scope:
        instance1 = scope.get(services.IServiceA)

    assert instance1.value == "disposed"


def test_scoped_pop_exception(services): ...
