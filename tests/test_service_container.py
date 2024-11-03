from abc import ABC
import pytest

from pyjudo import ServiceContainer, ServiceLife
from pyjudo.exceptions import (
    ServicesCircularDependencyError,
    ServicesResolutionError,
    ServicesRegistrationError,
)


# Mock services for testing
class IServiceA(ABC):
    value: str

class ServiceA(IServiceA):
    def __init__(self, value: str = "A"):
        self.value: str = value

    def dispose(self):
        self.value = "disposed"

class IServiceB(ABC):
    pass

class ServiceB(IServiceB):
    def __init__(self, service_a: IServiceA):
        self.service_a: IServiceA = service_a
        self.value: str = "B"

class IServiceC(ABC):
    pass

class ServiceC(IServiceC):
    def __init__(self, service_b: IServiceB, service_a: IServiceA):
        self.service_b: IServiceB = service_b
        self.service_a: IServiceA = service_a
        self.value: str = "C"

# Circular dependency example
class ServiceD(IServiceA):
    def __init__(self, service_c: IServiceC):
        self.service_c: IServiceC = service_c

def test_singleton_lifetime():
    container = ServiceContainer()
    container.register(IServiceA, ServiceA, ServiceLife.SINGLETON)

    instance1 = container.get(IServiceA)
    instance2 = container.get(IServiceA)

    assert instance1 is instance2
    assert instance1.value == "A"

def test_transient_lifetime():
    container = ServiceContainer()
    container.register(IServiceA, ServiceA, ServiceLife.TRANSIENT)

    instance1 = container.get(IServiceA)
    instance2 = container.get(IServiceA)

    assert instance1 is not instance2
    assert instance1.value == "A"
    assert instance2.value == "A"

def test_register_service():
    container = ServiceContainer()
    container.register(IServiceA, ServiceA)

    assert container.is_registered(IServiceA)

def test_get_resolved_service():
    container = ServiceContainer()
    container.register(IServiceA, ServiceA)
    container.register(IServiceB, ServiceB)

    service_b = container.get(IServiceB)

    assert isinstance(service_b, ServiceB)
    assert isinstance(service_b.service_a, ServiceA)
    assert service_b.value == "B"

def test_circular_dependency_detection():
    container = ServiceContainer()
    container.register(IServiceA, ServiceD)
    container.register(IServiceB, ServiceB)
    container.register(IServiceC, ServiceC)

    with pytest.raises(ServicesCircularDependencyError):
        _ = container.get(IServiceA)

def test_unregistered_service_resolution():
    container = ServiceContainer()

    with pytest.raises(ServicesResolutionError):
        _ = container.get(IServiceA)

def test_duplicate_registration():
    container = ServiceContainer()
    container.register(IServiceA, ServiceA)

    with pytest.raises(ServicesRegistrationError):
        container.register(IServiceA, ServiceA)

def test_overrides_in_transient():
    container = ServiceContainer()
    container.register(IServiceA, ServiceA, ServiceLife.TRANSIENT)

    # Overriding 'value' attribute for transient instance
    service_a = container.get(IServiceA, value="Overridden")

    assert service_a.value == "Overridden"

def test_overrides_in_singleton():
    container = ServiceContainer()
    container.register(IServiceA, ServiceA, ServiceLife.SINGLETON)

    # First instantiation without overrides
    instance1 = container.get(IServiceA)
    assert instance1.value == "A"

    # Singleton should prevent overrides after the instance is created
    with pytest.raises(ServicesResolutionError):
        _ = container.get(IServiceA, value="Should Fail")

def test_scoped_lifetime():
    container = ServiceContainer()
    container.register(IServiceA, ServiceA, ServiceLife.SCOPED)

    with container.create_scope() as scope:
        instance1 = scope.get(IServiceA)
        instance2 = scope.get(IServiceA)

        assert instance1 is instance2
        assert instance1.value == "A"

def test_scoped_lifetime_multiple_scopes():
    container = ServiceContainer()
    container.register(IServiceA, ServiceA, ServiceLife.SCOPED)

    with container.create_scope() as scope1:
        instance1 = scope1.get(IServiceA)

        with container.create_scope() as scope2:
            instance2 = scope2.get(IServiceA)

            assert instance1 is not instance2
            assert instance1.value == "A"
            assert instance2.value == "A"

def test_scoped_with_no_scope():
    container = ServiceContainer()
    container.register(IServiceA, ServiceA, ServiceLife.SCOPED)

    with pytest.raises(ServicesResolutionError):
        _ = container.get(IServiceA)

def test_scoped_with_disposable():
    container = ServiceContainer()
    container.register(IServiceA, ServiceA, ServiceLife.SCOPED)

    with container.create_scope() as scope:
        instance1 = scope.get(IServiceA)

    assert instance1.value == "disposed"