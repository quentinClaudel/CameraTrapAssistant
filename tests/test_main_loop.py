import sys
import threading
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "CameraTrapAssistant" / "src"
sys.path.insert(0, str(SRC_DIR))

from gui.utils.main_loop import MainLoopDispatcher


class FakeWidget:
    """Stands in for a Tk widget, recording what the main loop was asked to do."""

    def __init__(self):
        self.scheduled = []
        self.after_threads = []

    def after(self, delay, callback, *args):
        self.scheduled.append((delay, callback, args))
        self.after_threads.append(threading.current_thread())

    def run_next(self):
        """Run the pending drain, the way the Tk main loop eventually would."""
        _, callback, args = self.scheduled.pop()
        callback(*args)


class MainLoopDispatcherTests(unittest.TestCase):
    def setUp(self):
        self.widget = FakeWidget()
        self.dispatcher = MainLoopDispatcher(self.widget, interval_ms=10)

    def test_nothing_is_scheduled_before_start(self):
        self.dispatcher.post(lambda: None)
        self.assertEqual(self.widget.scheduled, [])

    def test_posting_never_touches_the_widget(self):
        """The whole point: a worker thread must not reach Tk at all."""
        self.dispatcher.start()
        self.widget.scheduled.clear()

        worker = threading.Thread(target=self.dispatcher.post, args=(lambda: None,))
        worker.start()
        worker.join(timeout=5)

        self.assertEqual(self.widget.scheduled, [])

    def test_posted_callbacks_run_on_the_next_drain(self):
        results = []
        self.dispatcher.start()
        self.dispatcher.post(results.append, "first")
        self.dispatcher.post(results.append, "second")

        self.widget.run_next()

        self.assertEqual(results, ["first", "second"])

    def test_drain_reschedules_itself(self):
        self.dispatcher.start()
        self.widget.run_next()

        self.assertEqual(len(self.widget.scheduled), 1)
        self.assertEqual(self.widget.scheduled[0][0], 10)

    def test_a_failing_callback_does_not_stop_the_queue(self):
        results = []

        def boom():
            raise RuntimeError("callback failed")

        self.dispatcher.start()
        self.dispatcher.post(boom)
        self.dispatcher.post(results.append, "still delivered")

        # The failure is reported rather than swallowed, and capturing it here
        # also keeps the traceback out of the release build log.
        with self.assertLogs(level="ERROR") as captured:
            self.widget.run_next()

        self.assertIn("callback failed", "\n".join(captured.output))
        self.assertEqual(results, ["still delivered"])
        self.assertEqual(len(self.widget.scheduled), 1)

    def test_stop_ends_the_polling(self):
        self.dispatcher.start()
        self.dispatcher.stop()

        self.widget.run_next()

        self.assertEqual(self.widget.scheduled, [])


if __name__ == "__main__":
    unittest.main()
