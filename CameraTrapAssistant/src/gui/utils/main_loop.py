"""Deliver work from worker threads to the Tk main loop."""

import logging
import queue


class MainLoopDispatcher:
    """Run callbacks posted by worker threads on the Tk main loop.

    Tkinter is not thread safe. CPython's ``_tkinter`` used to hide that for
    most uses: it forwarded a cross-thread call to the main loop, but only when
    Tcl described itself as threaded through ``tcl_platform(threaded)``. Tcl 9
    removed that variable, because threads are now always enabled, so
    ``_tkinter`` concludes the interpreter is unthreaded and evaluates the call
    inline on whichever thread made it. Two consequences were measured with the
    bundled Tk 9.0:

    - A dialog opened from a worker thread is an AppKit window created outside
      the main thread, and macOS terminates the process on the spot.
    - ``after()`` registers its timer against the calling thread, whose event
      queue nobody services, so the callback never runs at all. This is the
      quieter failure: no crash, and no logs either.

    A queue drained by a repeating poll that is only ever scheduled from the
    main loop depends on none of that, on any Tcl version and every platform.
    """

    def __init__(self, widget, interval_ms: int = 50):
        self._widget = widget
        self._interval_ms = interval_ms
        self._pending = queue.SimpleQueue()
        self._running = False

    def start(self) -> None:
        """Start draining. Call from the thread that runs the main loop."""
        if not self._running:
            self._running = True
            self._schedule()

    def stop(self) -> None:
        """Stop draining, for instance while the window is being torn down."""
        self._running = False

    def post(self, callback, *arguments) -> None:
        """Queue a callback to run on the main loop. Safe from any thread."""
        self._pending.put((callback, arguments))

    def _schedule(self) -> None:
        if self._running:
            self._widget.after(self._interval_ms, self._drain)

    def _drain(self) -> None:
        try:
            while True:
                try:
                    callback, arguments = self._pending.get_nowait()
                except queue.Empty:
                    break
                try:
                    callback(*arguments)
                except Exception:
                    # One failed callback must not stop the queue: the log
                    # handler and the completion dialogs share this drain.
                    logging.exception("A main loop callback raised")
        finally:
            # Always reschedule, including after a callback opened a modal
            # dialog that blocked the loop until the user dismissed it.
            self._schedule()
