import threading

from pyjudo.service_life import ServiceLife


class ServiceEntry[T]:
    """
    Represents a service entry in the container.
    """
    service_class: type[T]
    service_life: ServiceLife
    instance: T | None

    def __init__(self, service_class: type[T], service_life: ServiceLife):
        self.service_class = service_class
        self.service_life = service_life
        self.instance = None
        self.lock = threading.Lock()