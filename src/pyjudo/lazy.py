import threading
from typing import Any, Protocol

from pyjudo.iservice_container import IServiceContainer


class Lazy[T](Protocol):
    def __call__(self, **kwargs: Any) -> T: ...

    def __getattr__(self, name: str) -> Any: ...

    def __repr__(self) -> str: ...

    
class LazyProxy[T](Lazy[T]):
    _container: IServiceContainer
    _service_class: type[T]
    _instance: T | None
    _lock: threading.Lock

    def __init__(self, container: IServiceContainer, service_class: type[T]):
        self._container = container
        self._service_class = service_class
        self._instance = None
        self._lock = threading.Lock()
    
    def _resolve(self, **kwargs: Any) -> T:
        if self._instance is None:
            with self._lock:
                self._instance = self._container.get(self._service_class, **kwargs)
        return self._instance

    def __getattr__(self, name: str) -> Any:
        # If you try to get an attr before manually resolving the instance, it will resolve with no overrides
        instance = self._resolve()
        return getattr(instance, name)
    
    def __call__(self, **kwargs) -> T:
        return self._resolve(**kwargs)
    
    def __repr__(self) -> str:
        return f"<LazyProxy for {self._service_class.__name__}>"