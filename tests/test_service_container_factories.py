import pytest
from abc import ABC

from pyjudo import ServiceContainer
from pyjudo.exceptions import (
    ServiceCircularDependencyError,
    ServiceResolutionError,
    ServiceRegistrationError,
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

