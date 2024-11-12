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

def test_singleton_thread_safety(services):
    import threading

    container = ServiceContainer()

    _ = container.register(services.ISingletonService, services.SingletonService, ServiceLife.SINGLETON)

    thread_count = 10
    results = []
    barrier = threading.Barrier(thread_count)
    lock = threading.Lock()

    def resolve_singleton():
        # Wait for all threads to be ready
        barrier.wait()
        service = container.get(services.ISingletonService)
        with lock:
            results.append(service)

    threads = [threading.Thread(target=resolve_singleton) for _ in range(thread_count)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Verify that all resolved services are the same instance
    first_instance = results[0]
    assert all(service is first_instance for service in results[1:]), "Singleton instances are not the same across threads."

    # Verify that only one instance was created
    instance_count = services.SingletonService.get_instance_count()
    assert instance_count == 1, f"SingletonService was instantiated {instance_count} times instead of once."