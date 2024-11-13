import logging
import threading
from typing import override

from pyjudo.core import IServiceScope, IScopeStack
from pyjudo.exceptions import ServiceScopeError


class ScopeStack(IScopeStack):
    def __init__(self) -> None:
        self.__scopes_stack = threading.local()
        self.__lock = threading.Lock()
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @property
    def _scope_stack(self) -> list[IServiceScope]:
        if not hasattr(self.__scopes_stack, "scopes"):
            self.__scopes_stack.scopes = []
        return self.__scopes_stack.scopes

    @override
    def get_current(self) -> IServiceScope | None:
        with self.__lock:
            if not self._scope_stack:
                return None
            return self._scope_stack[-1]

    @override
    def push(self, scope: IServiceScope) -> None:
        with self.__lock:
            self._scope_stack.append(scope)
            self._logger.debug("Pushed new scope to stack.")

    @override
    def pop(self) -> None:
        with self.__lock:
            try:
                _ = self._scope_stack.pop()
                self._logger.debug("Popped scope from stack.")
            except IndexError:
                raise ServiceScopeError("No scope available to pop.")