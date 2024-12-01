"""
PyJudo: Simple dependency injection in Python.
"""

from pyjudo.core import IServiceContainer, ServiceLife
from .factory import Factory
from .service_container import ServiceContainer as ServiceContainerBase

def ServiceContainer() -> ServiceContainerBase:
    ...

__all__ = ["Factory", "ServiceContainer", "IServiceContainer", "ServiceLife"]
