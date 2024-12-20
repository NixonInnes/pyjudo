"""
This type stub file was generated by pyright.
"""

from typing import override
from pyjudo.core import IScopeStack, IServiceScope

class ScopeStack(IScopeStack):
    def __init__(self) -> None:
        ...
    
    @override
    def get_current(self) -> IServiceScope | None:
        ...
    
    @override
    def push(self, scope: IServiceScope) -> None:
        ...
    
    @override
    def pop(self) -> None:
        ...
    


