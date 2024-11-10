import pytest

from pyjudo import ServiceContainer, ServiceLife
from pyjudo.exceptions import ServiceResolutionError


def test_singleton_lifetime(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA, ServiceLife.SINGLETON)

    instance1 = container.get(services.IServiceA)
    instance2 = container.get(services.IServiceA)

    assert instance1 is instance2
    assert instance1.value == "A"

def test_overrides_in_singleton(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA, ServiceLife.SINGLETON)

    # First instantiation without overrides
    instance1 = container.get(services.IServiceA)
    assert instance1.value == "A"

    # Singleton should prevent overrides after the instance is created
    with pytest.raises(ServiceResolutionError):
        _ = container.get(services.IServiceA, value="Should Fail")