from abc import ABC, abstractmethod
import time
from types import SimpleNamespace
import pytest
import threading

from pyjudo.disposable import IDisposable

# Mock services for testing
class IServiceA(ABC):
    value: str

class IServiceB(ABC):
    service_a: IServiceA

class IServiceC(ABC):
    service_a: IServiceA
    service_b: IServiceB


class ServiceA(IServiceA):
    def __init__(self, value: str = "A"):
        self.value: str = value


class ServiceB(IServiceB):
    def __init__(self, service_a: IServiceA):
        self.service_a: IServiceA = service_a
        self.value: str = "B"


class ServiceC(IServiceC):
    def __init__(self, service_b: IServiceB, service_a: IServiceA):
        self.service_b: IServiceB = service_b
        self.service_a: IServiceA = service_a
        self.value: str = "C"


class CircularService(IServiceA):
    def __init__(self, service_c: IServiceC):
        self.service_c: IServiceC = service_c


class SoftDisposableService(IServiceA):
    def __init__(self):
        self.value = "A"

    def dispose(self):
        self.value = "disposed"


class HardDisposableService(IServiceA, IDisposable):
    def __init__(self):
        self.value = "A"

    def do_dispose(self):
        self.value = "disposed"


class ISingletonService(ABC):
    @abstractmethod
    def do_something(self) -> str:
        pass


class SingletonService(ISingletonService):
    _instance_count = 0
    _lock = threading.Lock()

    def __init__(self):
        with SingletonService._lock:
            SingletonService._instance_count += 1
        # Simulate some initialization delay
        time.sleep(0.1)

    def do_something(self) -> str:
        return "Singleton Service Operation"
    
    @classmethod
    def get_instance_count(cls) -> int:
        with cls._lock:
            return cls._instance_count

class IScopedService(ABC):
    @abstractmethod
    def do_something(self) -> str:
        pass

class IRepository(ABC):
    @abstractmethod
    def get_data(self) -> str:
        pass

class Repository(IRepository):
    def get_data(self) -> str:
        return "data"

class ScopedService(IScopedService):
    def __init__(self, repository: IRepository):
        self.repository = repository

    def do_something(self) -> str:
        return f"Scoped Service with {self.repository.get_data()}"

class ITransientService(ABC):
    @abstractmethod
    def do_something(self) -> str:
        pass

class TransientService(ITransientService):
    def __init__(self):
        # Simulate some initialization delay
        time.sleep(0.05)

    def do_something(self) -> str:
        return "Transient Service Operation"



@pytest.fixture
def services():
    return SimpleNamespace(
        IServiceA=IServiceA,
        IServiceB=IServiceB,
        IServiceC=IServiceC,
        ISingletonService=ISingletonService,
        IScopedService=IScopedService,
        ITransientService=ITransientService,
        IRepository=IRepository,
        ServiceA=ServiceA,
        ServiceB=ServiceB,
        ServiceC=ServiceC,
        CircularService=CircularService,
        SoftDisposableService=SoftDisposableService,
        HardDisposableService=HardDisposableService,
        SingletonService=SingletonService,
        ScopedService=ScopedService,
        TransientService=TransientService,
        Repository=Repository,
    )