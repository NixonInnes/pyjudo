from typing import Protocol, runtime_checkable


@runtime_checkable
class IDisposable(Protocol):
    def dispose(self) -> None: ...