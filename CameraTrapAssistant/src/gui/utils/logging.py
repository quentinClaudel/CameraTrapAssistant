import logging


class TkinterLogHandler(logging.Handler):
    """Write logs to a Tkinter Text widget without disrupting manual scrolling."""

    BOTTOM_TOLERANCE = 0.001

    def __init__(self, log_widget, on_unread_change=None, post_to_main_loop=None):
        super().__init__()
        self.log_widget = log_widget
        self.on_unread_change = on_unread_change
        # Analysis runs on a worker thread, so records arrive off the main
        # loop and must be handed to it rather than written directly. See
        # gui.utils.main_loop for why after() is not enough on its own.
        self.post_to_main_loop = post_to_main_loop or (
            lambda callback, *arguments: log_widget.after(0, callback, *arguments)
        )
        self.has_unread_logs = False

    def emit(self, record):
        msg = self.format(record)
        self.post_to_main_loop(self._append, msg)

    def _append(self, msg):
        should_follow = self._is_at_bottom()
        self.log_widget.config(state='normal')
        self.log_widget.insert('end', msg + '\n')
        self.log_widget.config(state='disabled')

        if should_follow:
            self.scroll_to_bottom()
        else:
            self._set_unread_logs(True)

    def _is_at_bottom(self):
        _, last_visible = self.log_widget.yview()
        return float(last_visible) >= 1.0 - self.BOTTOM_TOLERANCE

    def _set_unread_logs(self, has_unread_logs):
        if self.has_unread_logs == has_unread_logs:
            return
        self.has_unread_logs = has_unread_logs
        if self.on_unread_change:
            self.on_unread_change(has_unread_logs)

    def on_view_changed(self, _first_visible, last_visible):
        """Clear the unread indicator when the user returns to the bottom."""
        if float(last_visible) >= 1.0 - self.BOTTOM_TOLERANCE:
            self._set_unread_logs(False)

    def scroll_to_bottom(self):
        """Jump to the newest log entry and resume automatic scrolling."""
        self.log_widget.see('end')
        self._set_unread_logs(False)

    def clear(self):
        """Clear all logs and reset scrolling and unread state."""
        self.log_widget.config(state='normal')
        self.log_widget.delete('1.0', 'end')
        self.log_widget.config(state='disabled')
        self.scroll_to_bottom()
