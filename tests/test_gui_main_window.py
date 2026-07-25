import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch


SRC_DIR = Path(__file__).resolve().parents[1] / "CameraTrapAssistant" / "src"
sys.path.insert(0, str(SRC_DIR))

from gui import main_window


class FakeDispatcher:
    """Records what a worker thread hands back to the Tk main loop."""

    def __init__(self):
        self.scheduled = []

    def post(self, callback, *args):
        self.scheduled.append((callback, args))


class FakeButton:
    def __init__(self):
        self.states = []

    def config(self, **kwargs):
        if "state" in kwargs:
            self.states.append(kwargs["state"])


class RunInThreadTests(unittest.TestCase):
    """The worker thread must never touch Tk directly.

    A message box created outside the main thread is an AppKit window created
    outside the main thread, and that terminates the process on macOS.
    """

    def setUp(self):
        self.dispatcher = FakeDispatcher()
        self.run_btn = FakeButton()
        replacements = (
            ("main_loop_dispatcher", self.dispatcher),
            ("run_btn", self.run_btn),
        )
        for name, replacement in replacements:
            patcher = patch.object(main_window, name, replacement, create=True)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_worker(self, run_with_args):
        """Run run_in_thread on a real worker thread and return the dialogs."""
        with patch.object(main_window, "runWithArgs", run_with_args):
            with patch.object(main_window, "messagebox") as messagebox:
                worker = threading.Thread(
                    target=main_window.run_in_thread,
                    args=("/folder", object(), None, None),
                )
                worker.start()
                worker.join(timeout=30)
                self.assertFalse(worker.is_alive(), "the worker thread did not finish")
                return messagebox

    @staticmethod
    def failing_run(*_args):
        raise RuntimeError("no space left")

    def test_success_dialog_is_deferred_to_the_main_loop(self):
        messagebox = self.run_worker(lambda *args: None)

        messagebox.showinfo.assert_not_called()
        callback, _ = self.dispatcher.scheduled[0]
        self.assertIs(callback, messagebox.showinfo)

    def test_failure_dialog_is_deferred_to_the_main_loop(self):
        messagebox = self.run_worker(self.failing_run)

        messagebox.showerror.assert_not_called()
        callback, arguments = self.dispatcher.scheduled[0]
        self.assertIs(callback, messagebox.showerror)
        self.assertIn("no space left", arguments[1])

    def test_run_button_is_restored_after_a_successful_run(self):
        self.run_worker(lambda *args: None)

        restore, arguments = self.dispatcher.scheduled[-1]
        restore(*arguments)
        self.assertEqual(self.run_btn.states, ["normal"])

    def test_run_button_is_restored_after_a_failed_run(self):
        self.run_worker(self.failing_run)

        restore, arguments = self.dispatcher.scheduled[-1]
        restore(*arguments)
        self.assertEqual(self.run_btn.states, ["normal"])


if __name__ == "__main__":
    unittest.main()
