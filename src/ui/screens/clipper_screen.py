"""Clipper screen for Video Slice TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Input,
    Label,
    Static,
    DataTable,
    Checkbox,
    ProgressBar,
)
from textual import work
import asyncio
import os

from ui.components import ScreenBase
from logic import (
    parse_time,
    format_hhmmss,
    run_ffmpeg,
    Range,
    clean_video_path,
    get_output_directory,
    validate_output_path,
    ensure_output_dir,
    build_cut_command,
    generate_clip_filename,
    CLIPPER_OUTPUT_NAME,
)


class ClipperScreen(ScreenBase):
    """Screen for clipping videos into custom ranges."""

    CSS = (
        ScreenBase.CSS
        + """
    .input-section {
        height: auto;
    }
    .time-inputs {
        height: auto;
        margin: 1 0;
    }
    """
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ranges = []
        self._next_idx = 1
        self._custom_output_path = None

    def _compose_content(self) -> ComposeResult:
        with Vertical(classes="screen-container"):
            yield Static("🔪 MEDIA CLIPPER", classes="screen-title")

            with Vertical(classes="times-section"):
                yield Label("⏱️ Times", classes="section-header")
                with Horizontal(classes="time-inputs"):
                    with Vertical(classes="input-group"):
                        yield Label("⏱️ Start Time")
                        self.start_input = Input(placeholder="00:00:00")
                        yield self.start_input

                    with Vertical(classes="input-group"):
                        yield Label("⏱️ End Time")
                        self.end_input = Input(placeholder="End of video")
                        yield self.end_input

                    with Vertical(classes="input-group", id="add-btn-group"):
                        yield Label("")
                        yield Button("Add Range", id="add_range_btn", variant="success")

            with Vertical(classes="data-section"):
                yield Static("📋 CLIP QUEUE", classes="section-header")
                self.ranges_table = DataTable()
                self.ranges_table.add_columns("#", "Start", "End", "Duration")
                self.ranges_table.cursor_type = "row"
                yield self.ranges_table

                with Horizontal(classes="control-row"):
                    yield Button("Remove Selected", id="del_btn", variant="error")

            with Horizontal(classes="export-row"):
                self.reencode_cb = Checkbox("Precise Cut (Slower)", value=False)
                yield self.reencode_cb
                yield Button("START EXPORT", id="export_btn", variant="success")

            with Vertical(classes="progress-section"):
                self.progress_label = Static("")
                yield self.progress_label
                self.progress_bar = ProgressBar(total=100, show_eta=False)
                self.progress_bar.display = False
                yield self.progress_bar

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button

        if btn.id == "add_range_btn":
            self.add_range()

        elif btn.id == "del_btn":
            self.delete_selected_range()

        elif btn.id == "export_btn":
            self.export_clips()

    def on_input_changed(self, event: Input.Changed) -> None:
        pass

    def on_video_cleared(self) -> None:
        """Reset internal state and clear UI tables."""
        self._ranges = []
        self._next_idx = 1
        if hasattr(self, "ranges_table"):
            self.ranges_table.clear()

    async def load_video_info(self):
        """Override to load video info from hub's shared video path."""
        if not self.video_path:
            return

        path = self.video_path

        if not os.path.exists(path):
            self.show_status(f"❌ File not found: {path}", "error")
            return

        from logic import get_video_duration, format_hhmmss

        duration = await get_video_duration(path)
        if duration is not None:
            self._video_duration = duration
            self.show_status(
                f"✅ {os.path.basename(path)} loaded - {format_hhmmss(duration)}",
                "success",
            )
        else:
            self.show_status("⚠️ Could not get video duration", "warning")

    def add_range(self) -> None:
        start = self.start_input.value.strip()
        end = self.end_input.value.strip()

        if not start:
            self.show_status("⚠️ You must specify start time", "warning")
            return

        try:
            s = parse_time(start)

            if not end:
                if self._video_duration is None:
                    self.show_status(
                        "⚠️ Specify end time or load video to use auto end", "warning"
                    )
                    return
                e = self._video_duration
                self.show_status(f"ℹ️ Using auto end: {format_hhmmss(e)}", "warning")
            else:
                e = parse_time(end)

            if not self.video_path:
                self.show_status("⚠️ Load a video first", "warning")
                return

            r = Range(s, e, self._next_idx)
            self._next_idx += 1
            self._ranges.append(r)

            self.ranges_table.add_row(
                str(r.idx),
                format_hhmmss(r.start),
                format_hhmmss(r.end),
                f"{int(r.duration())}s",
            )

            self.show_status(f"✅ Range #{r.idx} added", "success")

            self.start_input.value = ""
            self.end_input.value = ""
            self.start_input.focus()

        except Exception as exc:
            self.show_status(f"❌ Error: {exc}", "error")

    def delete_selected_range(self):
        try:
            if self.ranges_table.row_count == 0:
                self.show_status("⚠️ No ranges to delete", "warning")
                return

            cursor_row = self.ranges_table.cursor_row
            row = self.ranges_table.get_row_at(cursor_row)
            idx = int(row[0])

            self._ranges = [r for r in self._ranges if r.idx != idx]

            self.ranges_table.clear()
            for r in self._ranges:
                self.ranges_table.add_row(
                    str(r.idx),
                    format_hhmmss(r.start),
                    format_hhmmss(r.end),
                    f"{int(r.duration())}s",
                )

            self.show_status(f"🗑️ Deleted range #{idx}", "warning")

        except Exception as exc:
            self.show_status(f"❌ Error deleting: {exc}", "error")

    def _get_output_directory(self) -> str:
        """Get the output directory, either custom or default."""
        return get_output_directory(
            self._custom_output_path, self.video_path, CLIPPER_OUTPUT_NAME
        )

    @work
    async def export_clips(self):
        if not self.video_path:
            self.show_status("⚠️ No video loaded", "warning")
            return

        video_path = clean_video_path(self.video_path)

        if not os.path.exists(video_path):
            self.show_status("❌ File not found for exporting", "error")
            return

        if not self._ranges:
            self.show_status("⚠️ No ranges to export", "warning")
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

        use_reencode = self.reencode_cb.value
        total = len(self._ranges)

        self.progress_bar.display = True
        self.progress_bar.update(total=total, progress=0)
        self.progress_label.update(f"🔄 Exporting 0/{total} clips...")

        self.show_status(f"🚀 Starting export of {total} clips to {out_dir}", "success")

        completed = 0
        extension = os.path.splitext(video_path)[1] or ".mp4"
        for r in self._ranges:
            out_name = generate_clip_filename(
                r.idx,
                r.start,
                r.end,
                format_hhmmss(r.start),
                format_hhmmss(r.end),
                extension=extension,
            ).replace(":", "-")
            out_path = os.path.join(out_dir, out_name)
            duration = r.end - r.start

            cmd = build_cut_command(
                video_path, r.start, duration, out_path, use_reencode
            )

            await run_ffmpeg(cmd, lambda text: None, r.idx, out_path)
            completed += 1

            self.progress_bar.update(progress=completed)
            self.progress_label.update(f"🔄 Exporting {completed}/{total} clips...")

        self.progress_bar.display = False
        self.progress_label.update("")

        self.show_status(
            f"✅ Export complete: {completed}/{total} clips saved in {out_dir}",
            "success",
        )
