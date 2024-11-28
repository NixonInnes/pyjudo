import threading
import unittest
from unittest.mock import Mock

from pyjudo.core import IServiceScope
from pyjudo.core.iservice_stack import IScopeStack
from pyjudo.exceptions import ServiceScopeError
from pyjudo.scope_stack import ScopeStack


class Test_ScopeStack(unittest.TestCase):
    def setUp(self):
        self.scope_stack: IScopeStack = ScopeStack() # pyright: ignore[reportUninitializedInstanceVariable]
        self.mock_scope: IServiceScope = Mock(spec=IServiceScope) # pyright: ignore[reportUninitializedInstanceVariable]

    def test_push_scope(self):
        self.scope_stack.push(self.mock_scope)

        self.assertEqual(self.scope_stack.get_current(), self.mock_scope)

    def test_pop_scope(self):
        self.scope_stack.push(self.mock_scope)
        self.scope_stack.pop()

        self.assertIsNone(self.scope_stack.get_current())

    def test_get_current_no_scope(self):
        self.assertIsNone(self.scope_stack.get_current())

    def test_pop_empty_stack(self):
        with self.assertRaises(ServiceScopeError):
            self.scope_stack.pop()

    def test_get_current_returns_last_pushed_scope(self):
        scope1 = Mock(spec=IServiceScope)
        scope2 = Mock(spec=IServiceScope)

        self.scope_stack.push(scope1)
        self.scope_stack.push(scope2)

        self.assertEqual(self.scope_stack.get_current(), scope2)

    def test_thread_safety(self):
        def worker(scope_stack, scope):
            scope_stack.push(scope)
            self.assertEqual(scope_stack.get_current(), scope)
            scope_stack.pop()

        threads = []
        for i in range(5):
            thread_scope = Mock(spec=IServiceScope)
            thread = threading.Thread(target=worker, args=(self.scope_stack, thread_scope))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.assertIsNone(self.scope_stack.get_current())