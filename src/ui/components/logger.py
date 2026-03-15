"""Logger component for displaying logs."""

from textual.widgets import Static


class Logger(Static):
    """A widget that displays log messages with automatic line limiting."""

    MAX_LINES = 20

    def write(self, text: str):
        """Append text to the log."""
        current = self.render()
        if not current:
            current = ""

        new_text = current + text
        lines = new_text.split("\n")
        if len(lines) > self.MAX_LINES:
            lines = lines[-self.MAX_LINES :]
            new_text = "\n".join(lines)

        self.update(new_text)

    def clear(self):
        """Clear the log."""
        self.update("")
