"""Compressor screen for batch conversion and compression with FFmpeg."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static, DataTable, Label, ProgressBar, Input, Checkbox
from textual import work
import os

from ui.components import ScreenBase
from logic import (
    run_ffmpeg,
    validate_output_path,
    ensure_output_dir,
    build_transcode_command,
    build_output_filename,
    list_media_files_from_directory,
    is_supported_media_file,
    COMPRESSOR_OUTPUT_NAME,
)


class CompressorScreen(ScreenBase):
    """Screen for batch compression and format conversion."""

    CSS = (
        ScreenBase.CSS
        + """
    .input-section, .output-section, .settings-section {
        height: auto;
        margin-bottom: 1;
    }
    .section-header {
        margin-bottom: 0;
        text-style: bold;
        color: $accent;
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
    .settings-grid {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1;
        height: auto;
    }
    .settings-grid > .input-group {
        height: auto;
    }
    """
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._videos = []
        self._custom_output_path = None

    def _compose_content(self) -> ComposeResult:
        with Vertical(classes="screen-container"):
            yield Static("🗜️ VIDEO COMPRESSOR", classes="screen-title")

            with Vertical(classes="input-section"):
                yield Label("📁 SOURCE FILES", classes="section-header")
                with Horizontal(classes="control-row"):
                    yield Button("Add Files", id="add_videos_btn", variant="primary")
                    yield Button("Add Folder", id="add_folder_btn", variant="primary")
                    yield Button("Clear Queue", id="clear_all_btn", variant="error")

            with Vertical(classes="data-section"):
                yield Static("📋 BATCH QUEUE", classes="section-header")
                self.videos_table = DataTable()
                self.videos_table.add_columns("File")
                self.videos_table.cursor_type = "row"
                yield self.videos_table

                with Horizontal(classes="control-row"):
                    yield Button("Remove Selected", id="del_video_btn", variant="error")

            with Vertical(classes="settings-section"):
                yield Label("⚙️ COMPRESSION SETTINGS", classes="section-header")
                with Vertical(classes="settings-grid"):
                    with Vertical(classes="input-group"):
                        yield Label("Output format (e.g. mp4, mov, mkv)")
                        self.format_input = Input(value="mp4")
                        yield self.format_input

                    with Vertical(classes="input-group"):
                        yield Label("CRF (lower = better quality, bigger file)")
                        self.crf_input = Input(value="23")
                        yield self.crf_input

                    with Vertical(classes="input-group"):
                        yield Label("Preset (ultrafast..veryslow)")
                        self.preset_input = Input(value="medium")
                        yield self.preset_input

                    with Vertical(classes="input-group"):
                        yield Label("Filename suffix")
                        self.suffix_input = Input(value="_compressed")
                        yield self.suffix_input

                self.scan_subdirs_cb = Checkbox("Scan subfolders when adding a directory", value=True)
                yield self.scan_subdirs_cb

            with Vertical(classes="output-section"):
                yield Label("📁 EXPORT ROUTE", classes="section-header")
                self.output_input = Input(placeholder="Path...", disabled=True)
                yield self.output_input

                with Horizontal(classes="control-row"):
                    yield Button("Select Folder", id="output_browse_btn", variant="primary")
                    yield Button("Use Source Folder", id="output_default_btn", variant="warning")

            with Horizontal(classes="export-row"):
                yield Button("START BATCH", id="export_btn", variant="success")

            with Vertical(classes="progress-section"):
                self.progress_label = Static("")
                yield self.progress_label
                self.progress_bar = ProgressBar(total=100, show_eta=False)
                self.progress_bar.display = False
                yield self.progress_bar

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id

        if btn == "add_videos_btn":

            def handle_files(file_paths):
                if file_paths:
                    if isinstance(file_paths, str):
                        self.add_videos([file_paths])
                    else:
                        self.add_videos(file_paths)

            self.open_file_dialog(handle_files, multi=True)

        elif btn == "add_folder_btn":

            def handle_folder(folder_path):
                if folder_path:
                    self.add_folder(folder_path)

            self.open_folder_dialog(handle_folder)

        elif btn == "clear_all_btn":
            self._videos = []
            self.videos_table.clear()
            self.show_status("🗑️ Queue cleared", "warning")

        elif btn == "del_video_btn":
            self.delete_selected_video()

        elif btn == "output_browse_btn":

            def handle_output(folder_path):
                if folder_path:
                    self._custom_output_path = folder_path
                    self.output_input.value = folder_path
                    self.output_input.disabled = False
                    self.show_status(f"📁 Output set to: {folder_path}", "success")

            self.open_folder_dialog(handle_output)

        elif btn == "output_default_btn":
            self._custom_output_path = None
            default_path = self._get_default_output_path()
            self.output_input.value = default_path
            self.output_input.disabled = True
            self.show_status(f"📁 Using source folder: {default_path}", "success")

        elif btn == "export_btn":
            self.compress_videos()

    def add_folder(self, folder_path: str) -> None:
        recursive = self.scan_subdirs_cb.value
        found = list_media_files_from_directory(folder_path, recursive=recursive)
        if not found:
            self.show_status("⚠️ No supported media files found in folder", "warning")
            return
        self.add_videos(found)

    def add_videos(self, file_paths: list[str]) -> None:
        added = 0
        for path in file_paths:
            if not is_supported_media_file(path):
                continue
            if path in self._videos:
                continue
            self._videos.append(path)
            self.videos_table.add_row(path)
            added += 1

        if added == 0:
            self.show_status("⚠️ No new supported files added", "warning")
            return

        if self._custom_output_path is None:
            self.output_input.value = self._get_default_output_path()
            self.output_input.disabled = True

        self.show_status(f"✅ Added {added} file(s)", "success")

    def delete_selected_video(self) -> None:
        try:
            if self.videos_table.row_count == 0:
                self.show_status("⚠️ No files to delete", "warning")
                return

            cursor_row = self.videos_table.cursor_row
            row = self.videos_table.get_row_at(cursor_row)
            path_to_delete = row[0]

            self._videos.remove(path_to_delete)
            self.videos_table.clear()
            for path in self._videos:
                self.videos_table.add_row(path)

            self.show_status(f"🗑️ Deleted: {os.path.basename(path_to_delete)}", "warning")
        except Exception as exc:
            self.show_status(f"❌ Error deleting: {exc}", "error")

    def _get_default_output_path(self) -> str:
        if self._videos:
            return os.path.dirname(self._videos[0])
        if self.video_path:
            return os.path.dirname(self.video_path)
        return os.path.join(os.getcwd(), COMPRESSOR_OUTPUT_NAME)

    def _get_output_directory(self) -> str:
        if self._custom_output_path:
            return self._custom_output_path
        return self._get_default_output_path()

    @work
    async def compress_videos(self) -> None:
        if not self._videos:
            self.show_status("⚠️ Add at least one file", "warning")
            return

        out_format = self.format_input.value.strip().lower().lstrip(".") or "mp4"
        suffix = self.suffix_input.value.strip() or "_compressed"

        try:
            crf = int(self.crf_input.value.strip())
        except ValueError:
            self.show_status("❌ CRF must be an integer", "error")
            return

        preset = self.preset_input.value.strip() or "medium"
        out_dir = self._get_output_directory()

        valid, error_msg = validate_output_path(out_dir)
        if not valid:
            self.show_status(f"❌ {error_msg}", "error")
            return

        if not ensure_output_dir(out_dir):
            self.show_status(f"❌ Could not create output directory: {out_dir}", "error")
            return

        total = len(self._videos)
        completed = 0
        failed = 0

        self.progress_bar.display = True
        self.progress_bar.update(total=total, progress=0)

        for idx, input_path in enumerate(self._videos, start=1):
            out_name = build_output_filename(input_path, suffix=suffix, extension=f".{out_format}")
            out_path = os.path.join(out_dir, out_name)

            cmd = build_transcode_command(
                input_path=input_path,
                output_path=out_path,
                crf=crf,
                preset=preset,
            )

            self.progress_label.update(f"🔄 Processing {idx}/{total}: {os.path.basename(input_path)}")
            success = await run_ffmpeg(cmd, lambda _: None, idx, out_path)

            if success:
                completed += 1
            else:
                failed += 1

            self.progress_bar.update(progress=idx)

        self.progress_bar.display = False
        self.progress_label.update("")

        if failed == 0:
            self.show_status(f"✅ Done! {completed}/{total} file(s) processed", "success")
        else:
            self.show_status(
                f"⚠️ Finished with errors. Success: {completed}, Failed: {failed}",
                "warning",
            )
