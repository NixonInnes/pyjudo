from abc import ABC
from types import SimpleNamespace
import pytest

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


@pytest.fixture
def services():
    return SimpleNamespace(
        IServiceA=IServiceA,
        IServiceB=IServiceB,
        IServiceC=IServiceC,
        ServiceA=ServiceA,
        ServiceB=ServiceB,
        ServiceC=ServiceC,
        CircularService=CircularService,
        SoftDisposableService=SoftDisposableService,
        HardDisposableService=HardDisposableService,
    )