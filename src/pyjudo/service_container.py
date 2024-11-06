import logging
import inspect
import threading
from typing import Any, Callable, get_args, get_origin, override, Self
from functools import partial

from pyjudo.exceptions import (
    ServicesCircularDependencyError,
    ServicesResolutionError,
    ServicesRegistrationError,
)
from pyjudo.iservice_container import IServiceContainer
from pyjudo.lazy import Lazy, LazyProxy
from pyjudo.service_entry import ServiceEntry
from pyjudo.service_life import ServiceLife
from pyjudo.service_scope import ServiceScope


class ServiceContainer(IServiceContainer):
    """
    A container for registering and resolving services with dependency injection.
    """

    def __init__(self):
        self.__lock = threading.Lock()
        self.__resolution_stack = threading.local()
        self.__scopes_stack = threading.local()

        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._services: dict[type[Any], ServiceEntry[Any]] = {}

        this_service_entry = ServiceEntry[Self](
            self.__class__,
            ServiceLife.SINGLETON,
        )
        this_service_entry.instance = self

        self._services[IServiceContainer] = this_service_entry
        self._logger.debug("Initialised service container")

    def _set_service[T](self, key: type[T], value: ServiceEntry[T]) -> None:
        with self.__lock:
            self._services[key] = value
    
    def _get_service[T](self, key: type[T]) -> ServiceEntry[T]:
        with self.__lock:
            try:
                return self._services[key]
            except KeyError:
                raise ServicesResolutionError(f"Unable to find service: {key}")

    @property
    def _scope_stack(self) -> list[ServiceScope]:
        if not hasattr(self.__scopes_stack, "scopes"):
            self.__scopes_stack.scopes = []
        return self.__scopes_stack.scopes

    @property
    def _resolution_stack(self) -> set[type]:
        if not hasattr(self.__resolution_stack, "stack"):
            self.__resolution_stack.stack = set()
            self._logger.debug("Initialized a new resolution stack for the thread.")
        return self.__resolution_stack.stack

    def _current_scope(self) -> ServiceScope | None:
        try:
            return self._scope_stack[-1]
        except IndexError:
            return None

    def _push_scope(self, scope: ServiceScope) -> None:
        with self.__lock:
            self._scope_stack.append(scope)
            self._logger.debug(f"Pushed new scope to stack.")

    def _pop_scope(self) -> None:
        with self.__lock:
            try:
                _ = self._scope_stack.pop()
                self._logger.debug(f"Popped scope from stack.")
            except IndexError:
                self._logger.warning("No scope to pop from stack.")

    @override
    def register[T](
        self,
        abstract_class: type[T],
        service_class: type[T],
        service_life: ServiceLife = ServiceLife.TRANSIENT,
    ) -> Self:
        """
        Registers a service class with the container.

        :param abstract_class: The abstract class or interface.
        :param service_class: The concrete implementation of abstract_class.
        :param service_life: The lifecycle of the service.
        """
        if abstract_class in self._services:
            raise ServicesRegistrationError(
                f"Service '{abstract_class.__name__}' is already registered."
            )

        assert issubclass(
            service_class, abstract_class
        ), f"'{service_class.__name__}' does not implement '{abstract_class.__name__}'"
        
        service = ServiceEntry[T](service_class, service_life)
        self._set_service(abstract_class, service)
        self._logger.debug(f"Registered service: {abstract_class.__name__} as {service_class.__name__} with life {service_life.name}")
        return self

    @override
    def add_transient[T](self, abstract_class: type[T], service_class: type[T]) -> Self:
        return self.register(abstract_class, service_class, ServiceLife.TRANSIENT)
    
    @override
    def add_scoped[T](self, abstract_class: type[T], service_class: type[T]) -> Self:
        return self.register(abstract_class, service_class, ServiceLife.SCOPED)
    
    @override
    def add_singleton[T](self, abstract_class: type[T], service_class: type[T]) -> Self:
        return self.register(abstract_class, service_class, ServiceLife.SINGLETON)

    @override
    def get[T](self, abstract_class: type[T], **overrides: Any) -> T: # pyright: ignore[reportAny]
        return self._resolve(abstract_class, scope=self._current_scope(), **overrides)

    def _resolve[T](self, abstract_class: type[T], scope: ServiceScope | None, **overrides: Any) -> T:
        if abstract_class in self._resolution_stack:
            raise ServicesCircularDependencyError(
                f"Circular dependency detected for '{abstract_class.__name__}'"
            )

        _ = self._resolution_stack.add(abstract_class)
        self._logger.debug(f"Resolving service '{abstract_class.__name__}'")

        try:
            service = self._get_service(abstract_class)

            match service.service_life:
                case ServiceLife.SINGLETON:
                    return self._get_singleton(service, **overrides)
                case ServiceLife.SCOPED:
                    if scope is None:
                        raise ServicesResolutionError(
                            f"Service '{abstract_class.__name__}' is scoped but no scope was provided."
                        )
                    return self._get_scoped(service, scope, **overrides)
                case ServiceLife.TRANSIENT:
                    return self._get_transient(service, **overrides)
        finally:
            self._resolution_stack.remove(abstract_class)

    def is_registered(self, abstract_class: type) -> bool:
        return abstract_class in self._services

    def _get_singleton[T](self, service_entry: ServiceEntry[T], **overrides: Any) -> T:
        if service_entry.instance is None:
            service_entry.instance = self._create_instance(service_entry, overrides)
        else:
            if overrides:
                raise ServicesResolutionError("Cannot use overrides with a singleton which has already been resolved.")
        return service_entry.instance

    def _get_scoped[T](self, service_entry: ServiceEntry[T], scope: ServiceScope, **overrides: Any) -> T:
        if scope.has_instance(service_entry.service_class):
            return scope.get_instance(service_entry.service_class)
        instance = self._create_instance(service_entry, overrides)
        scope.set_instance(service_entry.service_class, instance)
        return instance

    def _get_transient[T](self, service_entry: ServiceEntry[T], **overrides: Any) -> T:
        return self._create_instance(service_entry, overrides)

    def _create_instance[T](self, service_entry: ServiceEntry[T], overrides: dict[str, Any]) -> T:
        type_hints = inspect.signature(service_entry.service_class.__init__).parameters
        kwargs = {}
        for name, param in type_hints.items():
            if name == "self":
                continue

            # Skip *args and **kwargs
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue
            
            origin = get_origin(param.annotation)
            args = get_args(param.annotation)
            if origin is Lazy and args:
                service_class = args[0]
                kwargs[name] = LazyProxy(self, service_class)
                continue

            if name in overrides:
                kwargs[name] = overrides[name]
            elif param.annotation in self._services:
                kwargs[name] = self.get(param.annotation)
            elif param.default != inspect.Parameter.empty:
                kwargs[name] = param.default
            else:
                raise ServicesResolutionError(f"Unable to resolve dependency '{name}' for '{service_entry.service_class}'")
        
        self._logger.debug(f"Creating new instance of '{service_entry.service_class.__name__}'")
        return service_entry.service_class(**kwargs)

    def create_scope(self) -> ServiceScope:
        return ServiceScope(self)

    @override
    def __getitem__[T](self, key: type[T]) -> Callable[..., T]:
        return partial(self.get, key)