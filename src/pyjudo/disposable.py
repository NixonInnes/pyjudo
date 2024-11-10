from abc import ABC, abstractmethod
from typing import Any, Protocol, override, runtime_checkable

from pyjudo.exceptions import ServiceDisposedError

@runtime_checkable
class Disposable(Protocol):
    def dispose(self) -> None: ...


class IDisposable(ABC):
    """
    Represents an object that can be disposed.
    """
    __disposed: bool = False

    @abstractmethod
    def do_dispose(self) -> None:
        """
        Custom dispose logic should be implemented in subclasses.
        """
        pass

    def dispose(self) -> None:
        """
        Disposes of the object, setting its disposed state to True and calling the custom dispose logic.
        """
        if not self.__disposed:
            self.do_dispose()
            self.__disposed = True

    @property
    def is_disposed(self) -> bool:
        """
        Returns whether the object has been disposed.
        """
        return self.__disposed

    def _check_disposed(self) -> None:
        """
        Raises an exception if the object has been disposed.
        """
        if self.__disposed:
            raise ServiceDisposedError("Object is disposed and cannot be used.")

    def __getattr__(self, name: str): # pyright: ignore[reportAny]
        """
        Checks if the object is disposed before accessing any attributes.
        """
        self._check_disposed()
        return super().__getattribute__(name) # pyright: ignore[reportAny]

    @override
    def __getattribute__(self, name: str): # pyright: ignore[reportAny]
        """
        Checks if the object is disposed before accessing any attributes.
        """
        # Allow access to certain attributes to prevent recursion and allow checking if disposed.
        permitted_attrs = (
            "is_disposed",
            "_check_disposed", 
            "_IDisposable__disposed")
        if name not in permitted_attrs:
            self._check_disposed()
        return super().__getattribute__(name) # pyright: ignore[reportAny]

    @override
    def __setattr__(self, name: str, value: Any) -> None: # pyright: ignore[reportAny]
        """
        Checks if the object is disposed before setting any attributes.
        """
        self._check_disposed()
        super().__setattr__(name, value)

    def __call__(self, *args: Any, **kwargs: Any) -> Any: # pyright: ignore[reportAny]
        """
        Checks if the object is disposed before calling it.
        """
        self._check_disposed()
        return super().__call__(*args, **kwargs) # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]

    @override
    def __str__(self) -> str:
        """
        Checks if the object is disposed before converting it to a string.
        """
        self._check_disposed()
        return f"DISPOSED<{super().__str__()}>" if self.__disposed else super().__str__()

    @override
    def __repr__(self) -> str:
        """
        Checks if the object is disposed before getting its representation.
        """
        return f"DISPOSED<{super().__repr__()}>" if self.__disposed else super().__repr__()

    def __del__(self) -> None:
        """
        Ensures dispose is called before garbage collection if not already done.
        """
        if not self.__disposed:
            self.dispose()