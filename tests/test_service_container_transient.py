
from pyjudo import ServiceContainer, ServiceLife


def test_transient_lifetime(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA, ServiceLife.TRANSIENT)

    instance1 = container.get(services.IServiceA)
    instance2 = container.get(services.IServiceA)

    assert instance1 is not instance2
    assert instance1.value == "A"
    assert instance2.value == "A"


def test_overrides_in_transient(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA, ServiceLife.TRANSIENT)

    # Overriding 'value' attribute for transient instance
    service_a = container.get(services.IServiceA, value="Overridden")

    assert service_a.value == "Overridden"

def test_transient_dependencies(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA, ServiceLife.TRANSIENT)
    _ = container.register(services.IServiceB, services.ServiceB, ServiceLife.TRANSIENT)
    _ = container.register(services.IServiceC, services.ServiceC, ServiceLife.TRANSIENT)

    service_b = container.get(services.IServiceB)
    service_c = container.get(services.IServiceC)

    assert service_b.service_a is not service_c.service_a