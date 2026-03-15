from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import TabbedContent, TabPane, Static, Input, Button, Label
from textual.reactive import reactive
from textual.message import Message

from ui.screens.clipper_screen import ClipperScreen
from ui.screens.splitter_screen import SplitterScreen
from ui.screens.merger_screen import MergerScreen
from ui.screens.compressor_screen import CompressorScreen
from logic.input_parsing import clean_pasted_path
import os


class HubScreen(Container):
    """Main hub screen with tab navigation using TabbedContent."""

    shared_video_path = reactive("", always_update=True)
    shared_export_path = reactive("", always_update=True)

    CSS = """
    HubScreen {
        align: center middle;
        background: $boost;
    }
    #app-header {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
        border-bottom: thick $accent;
    }
    .hub-content {
        width: 80;
        height: auto;
        padding: 2;
        border: round $accent;
        background: $surface;
    }
    .hub-section {
        margin-bottom: 2;
        height: auto;
    }
    .hub-section > Label {
        margin-bottom: 0;
        text-style: bold;
        color: $accent;
    }
    .hub-section > Input {
        margin-bottom: 1;
        background: $boost;
    }
    .hub-row {
        height: 3;
        spacing: 1;
        align: center middle;
    }
    .hub-row > Button {
        margin: 0;
        height: 3;
    }
    #hub_browse_video_btn, #hub_browse_export_btn {
        width: 1fr;
    }
    #hub_clear_video_btn, #hub_clear_export_btn {
        width: 12;
    }
    .resize-warning {
        margin: 0 0 1 0;
        color: $text-muted;
        text-align: center;
        width: 100%;
        text-style: italic;
        background: $boost;
    }
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        padding: 1 2;
    }
    """

    class UpdateVideoPath(Message):
        """Message to update the shared video path."""

        def __init__(self, path: str) -> None:
            self.path = path
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Static("🗜️ VIDEO COMPRESSOR TUI", id="app-header")
        yield Label(
            "⚠️ Note: Resize terminal vertically if UI elements overlap.",
            classes="resize-warning",
        )

        with TabbedContent(initial="hub"):
            with TabPane("🏠 HUB", id="hub"):
                with Vertical(classes="hub-content"):
                    with Vertical(classes="hub-section"):
                        yield Label("🎬 MAIN MEDIA (VIDEO/AUDIO)")
                        self.hub_video_input = Input(
                            placeholder="No media selected...", disabled=True
                        )
                        yield self.hub_video_input
                        with Horizontal(classes="hub-row"):
                            yield Button(
                                "SELECT MEDIA", id="hub_browse_video_btn", variant="primary"
                            )
                            yield Button("REMOVE", id="hub_clear_video_btn", variant="error")

                    with Vertical(classes="hub-section"):
                        yield Label("📁 EXPORT TO")
                        self.hub_export_input = Input(
                            placeholder="Default path (video folder)...", disabled=True
                        )
                        yield self.hub_export_input
                        with Horizontal(classes="hub-row"):
                            yield Button(
                                "SELECT FOLDER", id="hub_browse_export_btn", variant="primary"
                            )
                            yield Button(
                                "REMOVE", id="hub_clear_export_btn", variant="error"
                            )


            with TabPane("✂️ Clipper", id="clipper"):
                yield ClipperScreen(id="clipper_screen")
            with TabPane("🔪 Splitter", id="splitter"):
                yield SplitterScreen(id="splitter_screen")
            with TabPane("🔗 Merger", id="merger"):
                yield MergerScreen(id="merger_screen")
            with TabPane("🗜️ Compressor", id="compressor"):
                yield CompressorScreen(id="compressor_screen")

    @property
    def tabbed_content(self) -> TabbedContent:
        return self.query_one(TabbedContent)

    @property
    def active_tab_id(self) -> str:
        return self.tabbed_content.active

    @active_tab_id.setter
    def active_tab_id(self, value: str) -> None:
        self.tabbed_content.active = value

    def on_mount(self) -> None:
        tabbed = self.tabbed_content
        tabbed.watch(tabbed, "active", self._on_tab_changed)

    def _on_tab_changed(self, value: str) -> None:
        if value == "hub":
            self.hub_video_input.value = self.shared_video_path
            self.hub_export_input.value = self.shared_export_path

    def on_paste(self, event: Message) -> None:
        """Handle drag and drop (terminal paste)."""
        path = clean_pasted_path(event.text)
        if path:
            self.shared_video_path = path

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id

        if btn == "hub_browse_video_btn":

            def handle_file(file_path):
                if file_path:
                    self.shared_video_path = file_path

            self.open_file_dialog(handle_file)

        elif btn == "hub_clear_video_btn":
            self.shared_video_path = ""

        elif btn == "hub_browse_export_btn":

            def handle_folder(folder_path):
                if folder_path:
                    self.shared_export_path = folder_path

            self.open_folder_dialog(handle_folder)

        elif btn == "hub_clear_export_btn":
            self.shared_export_path = ""


    def open_file_dialog(self, callback):
        """Open a native OS file selector using Tkinter in a separate thread."""
        import tkinter as tk
        from tkinter import filedialog
        import threading

        def run_dialog():
            try:
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                root.focus_force()

                file_path = filedialog.askopenfilename(
                    title="Select Media",
                    filetypes=[
                        ("Video files", "*.mp4 *.mkv *.avi *.mov *.m4v"),
                        ("Audio files", "*.mp3 *.wav *.flac *.m4a *.ogg"),
                        ("All files", "*.*"),
                    ],
                )
                if file_path:
                    self.app.call_from_thread(callback, file_path)

                root.destroy()
            except Exception as e:
                self.app.call_from_thread(self._show_error, f"Dialog Error: {str(e)}")

        thread = threading.Thread(target=run_dialog, daemon=True)
        thread.start()

    def open_folder_dialog(self, callback):
        """Open a native OS folder selector using Tkinter in a separate thread."""
        import tkinter as tk
        from tkinter import filedialog
        import threading

        def run_dialog():
            try:
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                root.focus_force()

                folder_path = filedialog.askdirectory(title="Select Output Folder")
                if folder_path:
                    self.app.call_from_thread(callback, folder_path)

                root.destroy()
            except Exception as e:
                self.app.call_from_thread(self._show_error, f"Dialog Error: {str(e)}")

        thread = threading.Thread(target=run_dialog, daemon=True)
        thread.start()

    def _show_error(self, message: str):
        self.notify(message, severity="error")

    def watch_shared_video_path(self, new_path: str) -> None:
        """Propagate shared video path to all screens."""
        self.hub_video_input.value = new_path

        for screen_id in ["clipper_screen", "splitter_screen"]:
            try:
                screen = self.query_one(f"#{screen_id}")
                if screen.video_path != new_path:
                    screen.video_path = new_path
            except:
                pass

        try:
            merger = self.query_one("#merger_screen")
            if new_path and new_path not in merger._videos:
                merger.add_videos([new_path])
            elif not new_path:
                merger._videos = []
                merger.videos_table.clear()
        except:
            pass

        try:
            compressor = self.query_one("#compressor_screen")
            if new_path:
                compressor.add_videos([new_path])
        except:
            pass

    def watch_shared_export_path(self, new_path: str) -> None:
        """Propagate shared export path to Clipper and Splitter."""
        self.hub_export_input.value = new_path

        for screen_id in ["clipper_screen", "splitter_screen"]:
            try:
                screen = self.query_one(f"#{screen_id}")
                screen._custom_output_path = new_path
            except:
                pass

    def on_hub_screen_update_video_path(self, message: UpdateVideoPath) -> None:
        """Handle update message from child screens."""
        self.shared_video_path = message.path
