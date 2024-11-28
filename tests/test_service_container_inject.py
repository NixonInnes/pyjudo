from abc import ABC
import unittest
from unittest.mock import MagicMock, Mock
from typing import Any, Callable

from pyjudo.core import IScopeStack, IServiceCache, IServiceEntryCollection, IServiceScope, IResolver, ServiceLife
from pyjudo.exceptions import ServiceRegistrationError, ServiceResolutionError, ServiceTypeError
from pyjudo.factory import FactoryProxy
from pyjudo.service_container import ServiceContainer

class IMockService(ABC): ...

class MockService(IMockService): ...

class Test_ServiceContainerInject(unittest.TestCase):
    def setUp(self):
        self.mock_service_entry_collection: IServiceEntryCollection = MagicMock(spec=IServiceEntryCollection)
        self.mock_singleton_cache: IServiceCache = Mock(spec=IServiceCache)
        self.mock_scope_stack: IScopeStack = Mock(spec=IScopeStack)
        self.mock_resolver: IResolver = Mock(spec=IResolver)
        self.mock_scope_factory: Callable[..., IServiceScope] = Mock(return_value=Mock(spec=IServiceScope))

        self.container = ServiceContainer(
            service_entry_collection=self.mock_service_entry_collection,
            singleton_cache=self.mock_singleton_cache,
            scope_stack=self.mock_scope_stack,
            scope_factory=self.mock_scope_factory,
            resolver=self.mock_resolver,
        )

    def test_inject_decorator(self):

        mock_service = MockService()
        self.mock_resolver.resolve_anonymous.return_value = mock_service

        self.container.register(IMockService, MockService, ServiceLife.SINGLETON)
        
        @self.container.inject
        def test_function(service: IMockService):
            return service

        rtn = test_function()
        self.assertEqual(rtn, mock_service)

    def test_inject_decorator_instance_method(self):
        mock_service = MockService()
        self.mock_resolver.resolve_anonymous.return_value = mock_service

        self.container.register(IMockService, MockService, ServiceLife.SINGLETON)

        class SomeClass:
            @self.container.inject
            def method(self, service: IMockService):
                return service

        instance = SomeClass()
        rtn = instance.method()
        self.assertEqual(rtn, mock_service)

    def test_inject_decorator_classmethod(self):
        mock_service = MockService()
        self.mock_resolver.resolve_anonymous.return_value = mock_service

        self.container.register(IMockService, MockService, ServiceLife.SINGLETON)

        class SomeClass:
            @self.container.inject
            @classmethod
            def method(cls, service: IMockService):
                return service

        rtn = SomeClass.method()
        self.assertEqual(rtn, mock_service)

    def test_inject_decorator_staticmethod(self):
        mock_service = MockService()
        self.mock_resolver.resolve_anonymous.return_value = mock_service

        self.container.register(IMockService, MockService, ServiceLife.SINGLETON)

        class SomeClass:
            @self.container.inject
            @staticmethod
            def method(service: IMockService):
                return service

        rtn = SomeClass.method()
        self.assertEqual(rtn, mock_service)