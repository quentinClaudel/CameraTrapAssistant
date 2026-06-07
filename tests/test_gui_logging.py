import logging
import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "CameraTrapAssistant" / "src"
sys.path.insert(0, str(SRC_DIR))

from gui.utils.logging import TkinterLogHandler


class FakeLogWidget:
    def __init__(self, view=(0.0, 1.0)):
        self.view = view
        self.contents = ""
        self.see_calls = []
        self.states = []

    def after(self, _delay, callback, *args):
        callback(*args)

    def config(self, **kwargs):
        if "state" in kwargs:
            self.states.append(kwargs["state"])

    def insert(self, _index, text):
        self.contents += text

    def delete(self, _start, _end):
        self.contents = ""

    def see(self, index):
        self.see_calls.append(index)
        self.view = (0.0, 1.0)

    def yview(self):
        return self.view


class TkinterLogHandlerTests(unittest.TestCase):
    def test_new_log_follows_when_view_is_at_bottom(self):
        widget = FakeLogWidget(view=(0.2, 1.0))
        unread_changes = []
        handler = TkinterLogHandler(widget, unread_changes.append)

        handler.emit(logging.LogRecord(
            "test", logging.INFO, "", 0, "First line", (), None
        ))

        self.assertEqual(widget.contents, "First line\n")
        self.assertEqual(widget.see_calls, ["end"])
        self.assertFalse(handler.has_unread_logs)
        self.assertEqual(unread_changes, [])

    def test_new_log_preserves_scrolled_view_and_marks_unread(self):
        widget = FakeLogWidget(view=(0.1, 0.7))
        unread_changes = []
        handler = TkinterLogHandler(widget, unread_changes.append)

        handler.emit(logging.LogRecord(
            "test", logging.INFO, "", 0, "New line", (), None
        ))

        self.assertEqual(widget.see_calls, [])
        self.assertTrue(handler.has_unread_logs)
        self.assertEqual(unread_changes, [True])

    def test_returning_to_bottom_clears_unread_indicator(self):
        widget = FakeLogWidget(view=(0.1, 0.7))
        unread_changes = []
        handler = TkinterLogHandler(widget, unread_changes.append)
        handler._set_unread_logs(True)

        handler.on_view_changed("0.4", "1.0")

        self.assertFalse(handler.has_unread_logs)
        self.assertEqual(unread_changes, [True, False])

    def test_clear_removes_logs_and_resets_view(self):
        widget = FakeLogWidget(view=(0.1, 0.7))
        widget.contents = "Old logs\n"
        unread_changes = []
        handler = TkinterLogHandler(widget, unread_changes.append)
        handler._set_unread_logs(True)

        handler.clear()

        self.assertEqual(widget.contents, "")
        self.assertEqual(widget.see_calls, ["end"])
        self.assertFalse(handler.has_unread_logs)
        self.assertEqual(unread_changes, [True, False])


if __name__ == "__main__":
    unittest.main()
