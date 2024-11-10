from collections.abc import Callable
import threading

from pyjudo.service_life import ServiceLife



class ServiceEntry[T]:
    """
    Represents a service entry in the container.
    """
    constructor: type[T] | Callable[..., T]
    service_life: ServiceLife
    instance: T | None
    lock: threading.Lock

    def __init__(self, constructor: type[T] | Callable[..., T], service_life: ServiceLife):
        self.constructor = constructor
        self.service_life = service_life
        self.instance = None
        self.lock = threading.Lock()