from typing import override
import gc
import unittest
from unittest.mock import MagicMock, patch

from pyjudo import disposable
from pyjudo.disposable import IDisposable
from pyjudo.exceptions import ServiceDisposedError


class DisposableClass(IDisposable):
    def __init__(self):
        self.x: int = 1
        self.disposed_values: list[int] = []

    def get_x(self) -> int:
        return self.x

    @override
    def do_dispose(self) -> None:
        self.disposed_values.append(self.x)
        self.x = None # pyright: ignore[reportAttributeAccessIssue]


class Test_Disposable(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.disposable: IDisposable = DisposableClass() #pyright: ignore[reportUninitializedInstanceVariable]

    def test_initial_state_not_disposed(self):
        """Test that the object is not disposed upon initialization."""
        self.assertFalse(self.disposable.is_disposed)

    def test_dispose_sets_is_disposed(self):
        """Test that calling dispose sets is_disposed to True."""
        self.disposable.dispose()
        self.assertTrue(self.disposable.is_disposed)

    def test_do_dispose_called_once(self):
        """Test that do_dispose is called exactly once upon disposal."""
        with patch.object(DisposableClass, 'do_dispose') as mock_do_dispose:
            disposable = DisposableClass()
            disposable.dispose()
            mock_do_dispose.assert_called_once()

            # Call dispose again
            disposable.dispose()
            mock_do_dispose.assert_called_once()  # Still only one call

    def test_attribute_access_raises_after_disposed(self):
        """Test that accessing disposed object raises an exception."""
        self.disposable.dispose()
        with self.assertRaises(ServiceDisposedError):
            _ = self.disposable.x

    def test_attribute_set_raises_after_disposed(self):
        """Test that setting an attribute on a disposed object raises an exception."""
        self.disposable.dispose()
        with self.assertRaises(ServiceDisposedError):
            self.disposable.x = 2
    
    def test_method_call_raises_after_disposed(self):
        """Test that calling a method on a disposed object raises an exception."""
        self.disposable.dispose()
        with self.assertRaises(ServiceDisposedError):
            _ = self.disposable.get_x()

    def test_dispose_multiple_times(self):
        """Test that multiple dispose calls do not raise errors and only dispose once."""
        self.disposable.dispose()
        self.disposable.dispose()
        self.disposable.dispose()
        self.assertTrue(self.disposable.is_disposed)

    def test_dispose_cleanup(self):
        """Test that dispose cleans up resources as expected."""
        self.assertEqual(self.disposable.x, 1)
        ref = self.disposable.__dict__
        self.disposable.dispose()
        self.assertIsNone(ref["x"])
        self.assertIn(1, ref["disposed_values"])

    def test_del_calls_dispose(self):
        """Test that __del__ calls dispose if not already disposed."""
        
        with patch.object(DisposableClass, 'dispose') as mock_dispose:
            disposable = DisposableClass()
            del disposable
            _ = gc.collect()  # Force garbage collection
            mock_dispose.assert_called_once()