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

    container = ServiceContainer()
    _ = container.add_transient(services.IServiceA, services.ServiceA)

    assert container.is_registered(services.IServiceA)

    container = ServiceContainer()
    _ = container.add_scoped(services.IServiceA, services.ServiceA)

    assert container.is_registered(services.IServiceA)

    container = ServiceContainer()
    _ = container.add_singleton(services.IServiceA, services.ServiceA)

    assert container.is_registered(services.IServiceA)


def test_get_resolved_service(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA)
    _ = container.register(services.IServiceB, services.ServiceB)

    service_b = container.get(services.IServiceB)

    assert isinstance(service_b, services.ServiceB)
    assert isinstance(service_b.service_a, services.ServiceA)
    assert service_b.value == "B"

    service_a_partial = container[services.IServiceA]

    assert callable(service_a_partial)
    service_a = service_a_partial()
    assert isinstance(service_a, services.ServiceA)


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

def test_registration_incorrect_type(services):
    container = ServiceContainer()

    with pytest.raises(ServiceRegistrationError):
        _ = container.register(services.IServiceA, services.ServiceB)

def test_unregister(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA)

    container.unregister(services.IServiceA)

    assert not container.is_registered(services.IServiceA)

def test_unregister_unregistered_service(services):
    container = ServiceContainer()

    with pytest.raises(ServiceRegistrationError):
        container.unregister(services.IServiceA)