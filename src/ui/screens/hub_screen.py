from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import TabbedContent, TabPane, Static, Input, Button, Label, DataTable, Checkbox
from textual.reactive import reactive
from textual.message import Message

from ui.screens.compressor_screen import CompressorScreen
from logic import list_media_files_from_directory, is_supported_media_file, COMPRESSOR_OUTPUT_NAME
from logic.input_parsing import clean_pasted_path
import os


class HubScreen(Container):
    """Main hub: source selection + export routing."""

    shared_video_path = reactive("", always_update=True)
    shared_export_path = reactive("", always_update=True)
    shared_source_paths = reactive(tuple(), always_update=True)

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
        width: 100;
        height: 1fr;
        padding: 1 2;
        border: round $accent;
        background: $surface;
    }
    #hub-scroll {
        height: 1fr;
    }
    .hub-section {
        margin-bottom: 1;
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
        width: 1fr;
    }
    .resize-warning {
        margin: 0 0 1 0;
        color: $text-muted;
        text-align: center;
        width: 100%;
        text-style: italic;
        background: $boost;
    }
    DataTable {
        min-height: 6;
        height: auto;
        margin: 1 0;
    }
    """

    class UpdateVideoPath(Message):
        """Compatibility message from old components."""

        def __init__(self, path: str) -> None:
            self.path = path
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Static("🗜️ VIDEO COMPRESSOR TUI", id="app-header")
        yield Label(
            "⚠️ Configure SOURCE + EXPORT in HUB, then tune settings in Compressor.",
            classes="resize-warning",
        )

        with TabbedContent(initial="hub"):
            with TabPane("🏠 HUB", id="hub"):
                with Vertical(classes="hub-content"):
                    with VerticalScroll(id="hub-scroll"):
                        with Vertical(classes="hub-section"):
                            yield Label("📁 SOURCE FILES")
                            self.hub_sources_input = Input(
                                placeholder="No files selected...", disabled=True
                            )
                            yield self.hub_sources_input

                            with Horizontal(classes="hub-row"):
                                yield Button("ADD FILES", id="hub_add_files_btn", variant="primary")
                                yield Button("ADD FOLDER", id="hub_add_folder_btn", variant="primary")
                                yield Button("CLEAR ALL", id="hub_clear_sources_btn", variant="error")

                            self.scan_subdirs_cb = Checkbox(
                                "Include subfolders when adding folder", value=True
                            )
                            yield self.scan_subdirs_cb

                            self.sources_table = DataTable()
                            self.sources_table.add_columns("Source file")
                            self.sources_table.cursor_type = "row"
                            yield self.sources_table

                            with Horizontal(classes="hub-row"):
                                yield Button(
                                    "REMOVE SELECTED",
                                    id="hub_del_source_btn",
                                    variant="error",
                                )

                        with Vertical(classes="hub-section"):
                            yield Label("📁 EXPORT TO")
                            self.hub_export_input = Input(
                                placeholder="Default: first source folder", disabled=True
                            )
                            yield self.hub_export_input
                            with Horizontal(classes="hub-row"):
                                yield Button(
                                    "SELECT FOLDER", id="hub_browse_export_btn", variant="primary"
                                )
                                yield Button(
                                    "USE DEFAULT", id="hub_clear_export_btn", variant="warning"
                                )

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

    def _get_default_export_path(self) -> str:
        if self.shared_source_paths:
            return os.path.dirname(self.shared_source_paths[0])
        return os.path.join(os.getcwd(), COMPRESSOR_OUTPUT_NAME)

    def _update_sources_summary(self) -> None:
        count = len(self.shared_source_paths)
        if count == 0:
            self.hub_sources_input.value = ""
            return
        if count == 1:
            self.hub_sources_input.value = self.shared_source_paths[0]
            return
        self.hub_sources_input.value = f"{count} files selected"

    def _sync_table(self) -> None:
        self.sources_table.clear()
        for path in self.shared_source_paths:
            self.sources_table.add_row(path)

    def _add_sources(self, paths: list[str]) -> None:
        current = set(self.shared_source_paths)
        changed = False
        for path in paths:
            if not is_supported_media_file(path):
                continue
            if path in current:
                continue
            current.add(path)
            changed = True

        if not changed:
            return

        ordered = tuple(sorted(current))
        self.shared_source_paths = ordered
        self.shared_video_path = ordered[0]

    def _remove_selected_source(self) -> None:
        if self.sources_table.row_count == 0:
            return
        try:
            cursor_row = self.sources_table.cursor_row
            row = self.sources_table.get_row_at(cursor_row)
            target = row[0]
        except Exception:
            return

        remaining = tuple(path for path in self.shared_source_paths if path != target)
        self.shared_source_paths = remaining
        self.shared_video_path = remaining[0] if remaining else ""

    def on_paste(self, event: Message) -> None:
        path = clean_pasted_path(event.text)
        if path:
            self._add_sources([path])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id

        if btn == "hub_add_files_btn":

            def handle_files(file_paths):
                if file_paths:
                    if isinstance(file_paths, str):
                        self._add_sources([file_paths])
                    else:
                        self._add_sources(list(file_paths))

            self.open_file_dialog(handle_files, multi=True)

        elif btn == "hub_add_folder_btn":

            def handle_folder(folder_path):
                if not folder_path:
                    return
                found = list_media_files_from_directory(
                    folder_path, recursive=self.scan_subdirs_cb.value
                )
                self._add_sources(found)

            self.open_folder_dialog(handle_folder)

        elif btn == "hub_clear_sources_btn":
            self.shared_source_paths = tuple()
            self.shared_video_path = ""

        elif btn == "hub_del_source_btn":
            self._remove_selected_source()

        elif btn == "hub_browse_export_btn":

            def handle_export(folder_path):
                if folder_path:
                    self.shared_export_path = folder_path

            self.open_folder_dialog(handle_export)

        elif btn == "hub_clear_export_btn":
            self.shared_export_path = ""
            self.hub_export_input.value = self._get_default_export_path()
            self.notify(f"Using default export path: {self.hub_export_input.value}")

    def open_file_dialog(self, callback, multi: bool = False):
        import tkinter as tk
        from tkinter import filedialog
        import threading

        def run_dialog():
            try:
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                root.focus_force()

                if multi:
                    file_paths = filedialog.askopenfilenames(
                        title="Select Media",
                        filetypes=[
                            ("Video files", "*.mp4 *.mkv *.avi *.mov *.m4v *.webm *.wmv"),
                            ("Audio files", "*.mp3 *.wav *.flac *.m4a *.ogg *.aac"),
                            ("All files", "*.*"),
                        ],
                    )
                    if file_paths:
                        self.app.call_from_thread(callback, list(file_paths))
                else:
                    file_path = filedialog.askopenfilename(
                        title="Select Media",
                        filetypes=[
                            ("Video files", "*.mp4 *.mkv *.avi *.mov *.m4v *.webm *.wmv"),
                            ("Audio files", "*.mp3 *.wav *.flac *.m4a *.ogg *.aac"),
                            ("All files", "*.*"),
                        ],
                    )
                    if file_path:
                        self.app.call_from_thread(callback, file_path)

                root.destroy()
            except Exception as exc:
                self.app.call_from_thread(self._show_error, f"Dialog Error: {str(exc)}")

        threading.Thread(target=run_dialog, daemon=True).start()

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

                folder_path = filedialog.askdirectory(title="Select Folder")
                if folder_path:
                    self.app.call_from_thread(callback, folder_path)

                root.destroy()
            except Exception as exc:
                self.app.call_from_thread(self._show_error, f"Dialog Error: {str(exc)}")

        threading.Thread(target=run_dialog, daemon=True).start()

    def _show_error(self, message: str):
        self.notify(message, severity="error")

    def watch_shared_source_paths(self, _: tuple) -> None:
        self._update_sources_summary()
        self._sync_table()

        if not self.shared_export_path:
            self.hub_export_input.value = self._get_default_export_path()

        try:
            compressor = self.query_one("#compressor_screen")
            compressor.source_paths = self.shared_source_paths
            compressor._refresh_summary()
        except Exception:
            pass

    def watch_shared_export_path(self, new_path: str) -> None:
        self.hub_export_input.value = new_path or self._get_default_export_path()

        try:
            compressor = self.query_one("#compressor_screen")
            compressor.export_path = new_path
            compressor._refresh_summary()
        except Exception:
            pass

    def on_hub_screen_update_video_path(self, message: UpdateVideoPath) -> None:
        if message.path:
            self._add_sources([message.path])
