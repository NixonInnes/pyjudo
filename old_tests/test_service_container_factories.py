from collections.abc import Callable
import pytest
from abc import ABC

from pyjudo import ServiceContainer, Factory

from pyjudo.exceptions import (
    ServiceRegistrationError,
    ServiceResolutionError,
    ServiceTypeError,
)


def test_factory_registration(services):
    container = ServiceContainer()

    def factory() -> services.IServiceA:
        return services.ServiceA("Factory")

    _ = container.register(services.IServiceA, factory)

    assert container.is_registered(services.IServiceA)

    instance = container.get(services.IServiceA)
    assert instance.value == "Factory"


def test_factory_registration_with_dependencies(services):
    container = ServiceContainer()

    class IAnotherService(ABC): ...

    class AnotherService(IAnotherService): ...

    def factory(another: IAnotherService) -> services.IServiceA:
        return services.ServiceA()

    _ = container.register(IAnotherService, AnotherService)
    _ = container.register(services.IServiceA, factory)

    instance = container.get(services.IServiceA)
    assert instance.value == "A"


def test_factory_registration_with_missing_dependencies(services):
    container = ServiceContainer()

    class IAnotherService(ABC): ...

    class AnotherService(IAnotherService): ...

    def factory(another: IAnotherService) -> services.IServiceA:
        return services.ServiceA()

    _ = container.register(services.IServiceA, factory)

    with pytest.raises(ServiceResolutionError):
        instance = container.get(services.IServiceA)


def test_factory_in_dependencies(services):
    container = ServiceContainer()

    class IAnotherService(ABC):
        factory: Callable[..., services.IServiceA]

    class AnotherService(IAnotherService):
        def __init__(self, factory: Factory[services.IServiceA]):
            self.factory = factory

    _ = container.register(services.IServiceA, services.ServiceA)
    _ = container.register(IAnotherService, AnotherService)

    instance = container.get(IAnotherService)

    assert callable(instance.factory)
    assert instance.factory.__repr__().startswith("FactoryProxy")

    service_a = instance.factory()

    assert isinstance(service_a, services.ServiceA)

def test_factory_registration_without_return_annotation(services):
    container = ServiceContainer()

    def factory():
        return services.ServiceA()

    with pytest.raises(ServiceRegistrationError):
        _ = container.register(services.IServiceA, factory)

def test_factory_registration_with_incorrect_return_annotation(services):
    container = ServiceContainer()

    def factory() -> services.IServiceB:
        return services.ServiceA()

    with pytest.raises(ServiceRegistrationError):
        _ = container.register(services.IServiceA, factory)
    

def test_factory_function_with_wrong_return_type(services):
    container = ServiceContainer()

    def factory() -> services.IServiceA:
        return "nonsense"

    _ = container.register(services.IServiceA, factory)

    with pytest.raises(ServiceTypeError):
        instance = container.get(services.IServiceA)


def test_factory_registration_not_class_or_callable(services):
    container = ServiceContainer()

    with pytest.raises(ServiceRegistrationError):
        _ = container.register(services.IServiceA, "Not a class or callable")

def test_get_factory(services):
    container = ServiceContainer()

    _ = container.register(services.IServiceA, services.ServiceA)

    factory = container.get_factory(services.IServiceA)

    assert callable(factory)

    instance = factory()

    assert isinstance(instance, services.ServiceA)

def test_get_factory_not_registered(services):
    container = ServiceContainer()

    with pytest.raises(ServiceResolutionError):
        factory = container.get_factory(services.IServiceA)