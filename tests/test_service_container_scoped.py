import pytest

from pyjudo import ServiceContainer, ServiceLife
from pyjudo.exceptions import ServiceResolutionError, ServiceScopeError, ServiceDisposedError


def test_scoped_lifetime(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA, ServiceLife.SCOPED)

    with container.create_scope() as scope:
        instance1 = scope.get(services.IServiceA)
        instance2 = scope.get(services.IServiceA)

        assert instance1 is instance2
        assert instance1.value == "A"

    with container.create_scope():
        instance3 = container.get(services.IServiceA)
        instance4 = container.get(services.IServiceA)

        assert instance3 is instance4
        assert instance3.value == "A"

    with container.create_scope() as scope:
        service_a_partial = scope[services.IServiceA]

        assert callable(service_a_partial)
        instance5 = service_a_partial()
        assert isinstance(instance5, services.ServiceA)

def test_scoped_lifetime_multiple_scopes(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA, ServiceLife.SCOPED)

    with container.create_scope() as scope1:
        instance1 = scope1.get(services.IServiceA)

        with container.create_scope() as scope2:
            instance2 = scope2.get(services.IServiceA)

            assert instance1 is not instance2
            assert instance1.value == "A"
            assert instance2.value == "A"


def test_scoped_with_no_scope(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA, ServiceLife.SCOPED)

    with pytest.raises(ServiceScopeError):
        _ = container.get(services.IServiceA)


def test_scoped_with_disposable(services):
    container = ServiceContainer()
    _ = container.register(
        services.IServiceA, services.SoftDisposableService, ServiceLife.SCOPED
    )

    with container.create_scope() as scope:
        instance1 = scope.get(services.IServiceA)

    assert instance1.value == "disposed"


def test_scoped_disposable(services):
    container = ServiceContainer()
    _ = container.register(
        services.IServiceA, services.HardDisposableService, ServiceLife.SCOPED
    )

    with container.create_scope() as scope:
        instance = scope.get(services.IServiceA)

    assert instance.is_disposed

    with pytest.raises(ServiceDisposedError):
        _ = instance.value

def test_scope_overrides(services):
    container = ServiceContainer()
    _ = container.register(services.IServiceA, services.ServiceA, ServiceLife.SCOPED)

    with container.create_scope() as scope:
        service_a = scope.get(services.IServiceA, value="Overridden")

        assert service_a.value == "Overridden"

    with container.create_scope() as scope:
        service_a = scope[services.IServiceA](value="Overridden")

        assert service_a.value == "Overridden"

    with container.create_scope():
        service_a = container.get(services.IServiceA, value="Overridden")

        assert service_a.value == "Overridden"

    with container.create_scope():
        service_a = container[services.IServiceA](value="Overridden")

        assert service_a.value == "Overridden"

    with container.create_scope() as scope:
        service_a = scope.get(services.IServiceA)

        assert service_a.value == "A"


def test_scoped_service_thread_safety(services):
    import threading

    container = ServiceContainer()

    _ = container.register(services.IScopedService, services.ScopedService, ServiceLife.SCOPED)
    _ = container.register(services.IRepository, services.Repository, ServiceLife.TRANSIENT)

    thread_count = 5
    results = []
    barrier = threading.Barrier(thread_count)
    lock = threading.Lock()

    def create_and_resolve_scope():
        # Wait for all threads to be ready
        barrier.wait()
        with container.create_scope() as scope:
            scoped_service = scope.get(services.IScopedService)
            with lock:
                results.append(scoped_service)

    threads = [threading.Thread(target=create_and_resolve_scope) for _ in range(thread_count)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Verify that all scoped services are unique instances
    unique_services = set(id(service) for service in results)
    assert len(unique_services) == thread_count, "ScopedService instances are not unique across scopes."