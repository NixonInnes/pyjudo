import pytest

from pyjudo import ServiceContainer
from pyjudo.exceptions import (
    ServiceCircularDependencyError,
    ServiceResolutionError,
    ServiceRegistrationError,
)


def test_register_service(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA)

    assert container.is_registered(services.IServiceA)


def test_get_resolved_service(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA)
    _ = container.register(services.IServiceB, services.ServiceB)

    service_b = container.get(services.IServiceB)

    assert isinstance(service_b, services.ServiceB)
    assert isinstance(service_b.service_a, services.ServiceA)
    assert service_b.value == "B"


def test_circular_dependency_detection(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.CircularService)
    _ = container.register(services.IServiceB, services.ServiceB)
    _ = container.register(services.IServiceC, services.ServiceC)

    with pytest.raises(ServiceCircularDependencyError):
        _ = container.get(services.IServiceA)


def test_unregistered_service_resolution(services):
    container = ServiceContainer()

    with pytest.raises(ServiceResolutionError):
        _ = container.get(services.IServiceA)


def test_duplicate_registration(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA)

    with pytest.raises(ServiceRegistrationError):
        _ = container.register(services.IServiceA, services.ServiceA)


