from collections.abc import Callable

from .service_life import ServiceLife


class ServiceEntry[T]:
    """
    Represents a service entry in the container.
    """

    constructor: type[T] | Callable[..., T]
    lifetime: ServiceLife

    def __init__(self, constructor: type[T] | Callable[..., T], lifetime: ServiceLife):
        self.constructor = constructor
        self.lifetime = lifetime