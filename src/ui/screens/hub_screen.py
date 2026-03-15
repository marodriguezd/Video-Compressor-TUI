from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import TabbedContent, TabPane, Static, Input, Button, Label
from textual.reactive import reactive
from textual.message import Message

from ui.screens.compressor_screen import CompressorScreen
from logic.input_parsing import clean_pasted_path


class HubScreen(Container):
    """Main hub for Video Compressor TUI."""

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
        """Message to update shared media path from child screens."""

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
                            placeholder="Default path (media folder)...", disabled=True
                        )
                        yield self.hub_export_input
                        with Horizontal(classes="hub-row"):
                            yield Button(
                                "SELECT FOLDER", id="hub_browse_export_btn", variant="primary"
                            )
                            yield Button("REMOVE", id="hub_clear_export_btn", variant="error")

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
            except Exception as exc:
                self.app.call_from_thread(self._show_error, f"Dialog Error: {str(exc)}")

        thread = threading.Thread(target=run_dialog, daemon=True)
        thread.start()

    def open_folder_dialog(self, callback):
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
            except Exception as exc:
                self.app.call_from_thread(self._show_error, f"Dialog Error: {str(exc)}")

        thread = threading.Thread(target=run_dialog, daemon=True)
        thread.start()

    def _show_error(self, message: str):
        self.notify(message, severity="error")

    def watch_shared_video_path(self, new_path: str) -> None:
        self.hub_video_input.value = new_path

        try:
            compressor = self.query_one("#compressor_screen")
            if new_path:
                compressor.add_videos([new_path])
        except Exception:
            pass

        try:
            compressor = self.query_one("#compressor_screen")
            if new_path:
                compressor.add_videos([new_path])
        except:
            pass

    def watch_shared_export_path(self, new_path: str) -> None:
        self.hub_export_input.value = new_path

        try:
            compressor = self.query_one("#compressor_screen")
            compressor._custom_output_path = new_path
            if new_path:
                compressor.output_input.value = new_path
                compressor.output_input.disabled = False
        except Exception:
            pass

    def on_hub_screen_update_video_path(self, message: UpdateVideoPath) -> None:
        self.shared_video_path = message.path
