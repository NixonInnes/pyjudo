
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

def test_transient_service_thread_safety(services):
    import threading

    container = ServiceContainer()

    _ = container.register(services.ITransientService, services.TransientService, ServiceLife.TRANSIENT)
    thread_count = 10
    results = []
    barrier = threading.Barrier(thread_count)
    lock = threading.Lock()

    def resolve_transient():
        # Wait for all threads to be ready
        barrier.wait()
        service = container.get(services.ITransientService)
        with lock:
            results.append(service)

    threads = [threading.Thread(target=resolve_transient) for _ in range(thread_count)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Verify that all transient services are unique instances
    unique_services = set(id(service) for service in results)
    assert len(unique_services) == thread_count, "TransientService instances are not unique across resolutions."