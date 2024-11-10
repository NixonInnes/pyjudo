import logging
import inspect
import threading
from typing import Any, Callable, cast, get_args, get_origin, override, Self
from functools import partial

from pyjudo.exceptions import (
    ServiceCircularDependencyError,
    ServiceResolutionError,
    ServiceRegistrationError,
    ServiceTypeError,
    ServiceScopeError,
)
from pyjudo.factory import Factory, FactoryProxy
from pyjudo.iservice_container import IServiceContainer
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
                raise ServiceResolutionError(f"Unable to find service: {key}")

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
        if not self._scope_stack:
            return None
        return self._scope_stack[-1]

    def _push_scope(self, scope: ServiceScope) -> None:
        with self.__lock:
            self._scope_stack.append(scope)
            self._logger.debug("Pushed new scope to stack.")

    def _pop_scope(self) -> None:
        with self.__lock:
            try:
                _ = self._scope_stack.pop()
                self._logger.debug("Popped scope from stack.")
            except IndexError:
                raise ServiceScopeError("No scope available to pop.")

    @override
    def register[T](
        self,
        abstract_class: type[T],
        constructor: type[T] | Callable[..., T],
        service_life: ServiceLife = ServiceLife.TRANSIENT,
    ) -> Self:
        """
        Registers a service class with the container.

        :param abstract_class: The abstract class or interface.
        :param service_class: The concrete implementation of abstract_class.
        :param service_life: The lifecycle of the service.
        """
        if abstract_class in self._services:
            raise ServiceRegistrationError(
                f"Service '{abstract_class.__name__}' is already registered."
            )

        if inspect.isclass(constructor):
            if not issubclass(constructor, abstract_class):
                raise ServiceRegistrationError(f"'{constructor.__name__}' does not implement '{abstract_class.__name__}'")
        elif callable(constructor):
            return_annotation = inspect.signature(constructor).return_annotation

            if return_annotation is inspect.Signature.empty:
                raise ServiceRegistrationError(f"Callable '{constructor.__name__}' must have a return annotation.")
            
            if not issubclass(return_annotation, abstract_class):
                raise ServiceRegistrationError(f"'{constructor.__name__}' does not return '{abstract_class.__name__}'")
        else:
            raise ServiceRegistrationError("Constructor must be a class or callable")

        service = ServiceEntry[T](constructor, service_life)
        self._set_service(abstract_class, service)
        self._logger.debug(f"Registered service: {abstract_class.__name__} as {constructor.__name__} with life {service_life.name}")
        return self

    @override
    def unregister(self, abstract_class: type) -> Self:
        with self.__lock:
            try:
                del self._services[abstract_class]
                self._logger.debug(f"Unregistered service: {abstract_class.__name__}")
            except KeyError:
                raise ServiceRegistrationError(f"Service '{abstract_class.__name__}' is not registered.")
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
        service = self._resolve(abstract_class, scope=self._current_scope(), **overrides)
        if not issubclass(type(service), abstract_class):
            raise ServiceTypeError(f"Service '{service}' is not of type '{abstract_class.__name__}'")
        return service

    def get_factory[T](self, abstract_class: type[T]) -> Callable[..., T]:
        if not self.is_registered(abstract_class):
            raise ServiceResolutionError(f"Service '{abstract_class.__name__}' is not registered.")
        return FactoryProxy(self, abstract_class)

    def _resolve[T](self, abstract_class: type[T], scope: ServiceScope | None, **overrides: Any) -> T:
        if abstract_class in self._resolution_stack:
            raise ServiceCircularDependencyError(
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
                        raise ServiceResolutionError(
                            f"Service '{abstract_class.__name__}' is scoped but no scope was provided."
                        )
                    return self._get_scoped(abstract_class, scope, service, **overrides)
                case ServiceLife.TRANSIENT:
                    return self._get_transient(service, **overrides)
        finally:
            self._resolution_stack.remove(abstract_class)

    @override
    def is_registered(self, abstract_class: type) -> bool:
        return abstract_class in self._services

    def _get_singleton[T](self, service_entry: ServiceEntry[T], **overrides: Any) -> T:
        if service_entry.instance is None:
            service_entry.instance = self._create_instance(service_entry, overrides)
        else:
            if overrides:
                raise ServiceResolutionError("Cannot use overrides with a singleton which has already been resolved.")
        return service_entry.instance

    def _get_scoped[T](self, abstract_class: type[T], scope: ServiceScope, service_entry: ServiceEntry[T], **overrides: Any) -> T:
        if scope.has_instance(abstract_class):
            return scope.get_instance(abstract_class)
        instance = self._create_instance(service_entry, overrides)
        scope.set_instance(abstract_class, instance)
        return instance

    def _get_transient[T](self, service_entry: ServiceEntry[T], **overrides: Any) -> T:
        return self._create_instance(service_entry, overrides)

    def _create_instance[T](self, service_entry: ServiceEntry[T], overrides: dict[str, Any]) -> T:
        if inspect.isclass(service_entry.constructor):
            type_hints = inspect.signature(service_entry.constructor.__init__).parameters
        else:
            type_hints = inspect.signature(service_entry.constructor).parameters
        
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
            if origin is Factory and args:
                abstract_class = args[0]
                kwargs[name] = FactoryProxy(self, abstract_class)
                continue

            if name in overrides:
                kwargs[name] = overrides[name]
            elif param.annotation in self._services:
                kwargs[name] = self.get(param.annotation)
            elif param.default != inspect.Parameter.empty:
                kwargs[name] = param.default
            else:
                raise ServiceResolutionError(f"Unable to resolve dependency '{name}' for '{service_entry.constructor}'")
        
        self._logger.debug(f"Creating new instance of '{T}'")

        return cast(T, service_entry.constructor(**kwargs)) # TODO: Remove cast

    def create_scope(self) -> ServiceScope:
        return ServiceScope(self)

    @override
    def __getitem__[T](self, key: type[T]) -> Callable[..., T]:
        return partial(self.get, key)