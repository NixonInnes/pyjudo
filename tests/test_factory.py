from abc import ABC, abstractmethod
from typing import Any, Callable
import unittest

from pyjudo.core import IResolver
from pyjudo.factory import FactoryProxy


class IFooService(ABC): ...


class FooService(IFooService): ...


class MockResolver(IResolver):
    services: dict[Any, Any] = {IFooService: FooService}

    def resolve[T](
        self, interface: type[T], overrides: dict[str, Any], binding: Any | None = None
    ) -> T:
        overrides = overrides or {}
        return self.services[interface](**overrides)

    def resolve_anonymous[T](
        self,
        constructor: Callable[..., T],
        overrides: dict[str, Any],
        binding: Any | None = None,
    ) -> T:
        raise NotImplementedError()


class Test_Factory(unittest.TestCase):
    def setUp(self):
        self.factory = FactoryProxy(MockResolver(), IFooService) # pyright: ignore[reportUninitializedInstanceVariable]

    def test_call_factory(self):
        foo = self.factory()

        self.assertIsInstance(foo, FooService)
