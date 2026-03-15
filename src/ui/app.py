"""Video Compressor TUI main application."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

from ui.screens import HubScreen


class VideoSliceApp(App):
    """Main application class for Video Compressor TUI."""

    CSS = """
    Screen {
        align: center middle;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "quit", "Quit"),
    ]

    def __init__(self, start_tab: str = None, video_path: str = None, **kwargs):
        super().__init__(**kwargs)
        self.start_tab = start_tab
        self.start_video_path = video_path

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield HubScreen()
        yield Footer()

    async def on_mount(self) -> None:
        if self.start_video_path and self.start_tab:
            hub = self.query_one(HubScreen)
            hub.active_tab = self.start_tab

            content = hub.query_one(f"#{self.start_tab}_screen")
            if content and hasattr(content, "video_path"):
                content.video_path = self.start_video_path
                await content.load_video_info()
