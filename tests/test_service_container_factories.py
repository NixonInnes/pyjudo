from collections.abc import Callable
import pytest
from abc import ABC

from pyjudo import ServiceContainer, Factory

from pyjudo.exceptions import (
    ServiceResolutionError,
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
        factory: Callable

    class AnotherService(IAnotherService):
        def __init__(self, factory: Factory[services.IServiceA]):
            self.factory = factory

    _ = container.register(services.IServiceA, services.ServiceA)
    _ = container.register(IAnotherService, AnotherService)

    instance = container.get(IAnotherService)

    assert callable(instance.factory)

    service_a = instance.factory()

    assert isinstance(service_a, services.ServiceA)
