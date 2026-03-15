"""Merger screen for Video Slice TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static, DataTable, Label, ProgressBar, Input
from textual import work
import asyncio
import os

from ui.components import ScreenBase
from logic import (
    run_ffmpeg,
    validate_output_path,
    ensure_output_dir,
    build_concat_command,
    MERGER_OUTPUT_NAME,
)


class MergerScreen(ScreenBase):
    """Screen for merging multiple videos into one."""

    CSS = (
        ScreenBase.CSS
        + """
    .input-section, .output-section {
        height: auto;
        margin-bottom: 1;
    }
    .section-header {
        margin-bottom: 0;
        text-style: bold;
        color: $accent;
    }
    .input-section > .control-row {
        margin-top: 1;
    }
    .output-section > Input {
        margin-bottom: 1;
        background: $boost;
    }
    .control-row {
        height: 3;
        spacing: 1;
        align: center middle;
    }
    .control-row > Button {
        margin: 0;
        height: 3;
        width: 1fr;
    }
    """
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._videos = []
        self._custom_output_path = None

    def _compose_content(self) -> ComposeResult:
        with Vertical(classes="screen-container"):
            yield Static("🔗 MEDIA MERGER", classes="screen-title")

            with Vertical(classes="input-section"):
                yield Label("📁 SOURCE FILES", classes="section-header")
                with Horizontal(classes="control-row"):
                    yield Button("Add Media", id="add_videos_btn", variant="primary")
                    yield Button("Clear All", id="clear_all_btn", variant="error")

            with Vertical(classes="data-section"):
                yield Static("📋 MERGE QUEUE", classes="section-header")
                self.videos_table = DataTable()
                self.videos_table.add_columns("Path")
                self.videos_table.cursor_type = "row"
                yield self.videos_table

                with Horizontal(classes="control-row"):
                    yield Button("Remove Selected", id="del_video_btn", variant="error")

            with Vertical(classes="output-section"):
                yield Label("📁 EXPORT ROUTE", classes="section-header")
                self.output_input = Input(placeholder="Path...", disabled=True)
                yield self.output_input

                with Horizontal(classes="control-row"):
                    yield Button(
                        "Select Folder", id="output_browse_btn", variant="primary"
                    )
                    yield Button(
                        "Use Default", id="output_default_btn", variant="error"
                    )

            with Horizontal(classes="export-row"):
                yield Button("START MERGE", id="export_btn", variant="success")

            with Vertical(classes="progress-section"):
                self.progress_label = Static("")
                yield self.progress_label
                self.progress_bar = ProgressBar(total=100, show_eta=False)
                self.progress_bar.display = False
                yield self.progress_bar

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button

        if btn.id == "add_videos_btn":

            def handle_files(file_paths):
                if file_paths:
                    if isinstance(file_paths, str):
                        self.add_videos([file_paths])
                    else:
                        self.add_videos(file_paths)

            self.open_file_dialog(handle_files, multi=True)

        elif btn.id == "clear_all_btn":
            self._videos = []
            self.videos_table.clear()
            self._custom_output_path = None
            self.show_status("🗑️ All videos cleared from queue", "warning")

            if hasattr(self, "output_input"):
                default_path = self._get_default_output_path()
                self.output_input.value = default_path
                self.output_input.disabled = True

            from ui.screens.hub_screen import HubScreen

            self.post_message(HubScreen.UpdateVideoPath(""))

        elif btn.id == "del_video_btn":
            self.delete_selected_video()

        elif btn.id == "export_btn":
            self.merge_videos()

        elif btn.id == "output_browse_btn":

            def handle_folder(folder_path):
                if folder_path:
                    self._custom_output_path = folder_path
                    self.output_input.value = folder_path
                    self.output_input.disabled = False
                    self.show_status(f"📁 Output set to: {folder_path}", "success")

            self.open_folder_dialog(handle_folder)

        elif btn.id == "output_default_btn":
            self._custom_output_path = None
            default_path = self._get_default_output_path()
            self.output_input.value = default_path
            self.output_input.disabled = True
            self.show_status(f"📁 Using default output: {default_path}", "success")

    def _get_default_output_path(self) -> str:
        """Get the default output directory path."""
        if self._videos:
            base_dir = os.path.dirname(self._videos[0])
            return os.path.join(base_dir, MERGER_OUTPUT_NAME)
        return os.path.join(os.getcwd(), MERGER_OUTPUT_NAME)

    def _get_output_directory(self) -> str:
        """Get the output directory, either custom or default."""
        if self._custom_output_path:
            return self._custom_output_path
        return self._get_default_output_path()

    def add_videos(self, file_paths) -> None:
        for path in file_paths:
            self._videos.append(path)
            self.videos_table.add_row(path)

        count = len(file_paths)
        self.show_status(f"✅ Added {count} video(s)", "success")

        if self._custom_output_path is None and hasattr(self, "output_input"):
            default_path = self._get_default_output_path()
            self.output_input.value = default_path
            self.output_input.disabled = True

    def delete_selected_video(self):
        try:
            if self.videos_table.row_count == 0:
                self.show_status("⚠️ No videos to delete", "warning")
                return

            cursor_row = self.videos_table.cursor_row
            row = self.videos_table.get_row_at(cursor_row)
            path_to_delete = row[0]

            self._videos.remove(path_to_delete)

            self.videos_table.clear()
            for path in self._videos:
                self.videos_table.add_row(path)

            self.show_status(
                f"🗑️ Deleted: {os.path.basename(path_to_delete)}", "warning"
            )

        except Exception as exc:
            self.show_status(f"❌ Error deleting: {exc}", "error")

    @work
    async def merge_videos(self):
        if len(self._videos) < 2:
            self.show_status("⚠️ You need at least two videos to merge", "warning")
            return

        out_dir = self._get_output_directory()

        valid, error_msg = validate_output_path(out_dir)
        if not valid:
            self.show_status(f"❌ {error_msg}", "error")
            return

        if not ensure_output_dir(out_dir):
            self.show_status(
                f"❌ Could not create output directory: {out_dir}", "error"
            )
            return

        extension = os.path.splitext(self._videos[0])[1] or ".mp4"
        out_path = os.path.join(out_dir, f"merged_file{extension}")

        list_path = os.path.join(out_dir, "filelist.txt")
        try:
            with open(list_path, "w") as f:
                for video_path in self._videos:
                    f.write(f"file '{video_path}'\n")

            self.progress_bar.display = True
            self.progress_bar.update(total=1, progress=0)
            self.progress_label.update("🔄 Merging videos...")
            self.show_status("🔄 Merging videos...", "success")

            cmd = build_concat_command(list_path, out_path)

            success = await run_ffmpeg(cmd, lambda text: None, 1, out_path)

            self.progress_bar.display = False
            self.progress_label.update("")

            if success:
                self.show_status(f"✅ Merge complete! Saved to: {out_path}", "success")
            else:
                self.show_status("❌ Merge failed", "error")
        except Exception as exc:
            self.show_status(f"❌ Error during merge: {exc}", "error")
        finally:
            try:
                os.remove(list_path)
            except OSError:
                pass
