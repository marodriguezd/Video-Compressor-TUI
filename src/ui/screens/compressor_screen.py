"""Compressor settings screen for batch conversion/compression with FFmpeg."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static, Label, ProgressBar, Input, Select
from textual import work
import os

from ui.components import ScreenBase
from logic import (
    run_ffmpeg,
    validate_output_path,
    ensure_output_dir,
    build_transcode_command,
    build_output_filename,
    COMPRESSOR_OUTPUT_NAME,
)


QUALITY_PROFILES = {
    "high": 18,
    "balanced": 23,
    "small": 28,
    "tiny": 32,
}


class CompressorScreen(ScreenBase):
    """Screen with compression settings and batch execution."""

    source_paths = tuple()
    export_path = ""

    CSS = (
        ScreenBase.CSS
        + """
    .settings-section {
        height: auto;
        margin-bottom: 1;
    }
    .summary-box {
        border: round $primary;
        padding: 1;
        margin-bottom: 1;
        background: $boost;
        height: auto;
    }
    .summary-box > Static {
        margin-bottom: 1;
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
    .settings-grid Label {
        margin-bottom: 1;
        text-style: bold;
        color: $accent;
    }
    Select, Input {
        width: 1fr;
    }
    """
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _compose_content(self) -> ComposeResult:
        with Vertical(classes="screen-container"):
            yield Static("🗜️ COMPRESSOR SETTINGS", classes="screen-title")

            with Vertical(classes="summary-box"):
                self.summary_sources = Static("Sources: 0 files")
                self.summary_export = Static("Export: default (source folder)")
                yield self.summary_sources
                yield self.summary_export

            with Vertical(classes="settings-section"):
                with Vertical(classes="settings-grid"):
                    with Vertical(classes="input-group"):
                        yield Label("Output format")
                        self.format_select = Select(
                            [("MP4", "mp4"), ("MOV", "mov"), ("MKV", "mkv"), ("WEBM", "webm")],
                            value="mp4",
                        )
                        yield self.format_select

                    with Vertical(classes="input-group"):
                        yield Label("Quality profile")
                        self.quality_select = Select(
                            [
                                ("High quality", "high"),
                                ("Balanced", "balanced"),
                                ("Small size", "small"),
                                ("Tiny size", "tiny"),
                            ],
                            value="balanced",
                        )
                        yield self.quality_select

                    with Vertical(classes="input-group"):
                        yield Label("Encoding speed preset")
                        self.preset_select = Select(
                            [
                                ("fast", "fast"),
                                ("medium", "medium"),
                                ("slow", "slow"),
                            ],
                            value="medium",
                        )
                        yield self.preset_select

                    with Vertical(classes="input-group"):
                        yield Label("Filename suffix")
                        self.suffix_input = Input(value="_compressed")
                        yield self.suffix_input

            with Horizontal(classes="export-row"):
                yield Button("START BATCH", id="export_btn", variant="success")

            with Vertical(classes="progress-section"):
                self.progress_label = Static("")
                yield self.progress_label
                self.progress_bar = ProgressBar(total=100, show_eta=False)
                self.progress_bar.display = False
                yield self.progress_bar

    async def on_mount(self) -> None:
        await super().on_mount()
        try:
            from ui.screens.hub_screen import HubScreen

            hub = self.app.query_one(HubScreen)
            self.source_paths = hub.shared_source_paths
            self.export_path = hub.shared_export_path
            self.watch(hub, "shared_source_paths", self._on_hub_sources_changed)
            self.watch(hub, "shared_export_path", self._on_hub_export_changed)
            self._refresh_summary()
        except Exception:
            pass

    def _on_hub_sources_changed(self, paths: tuple) -> None:
        self.source_paths = paths
        self._refresh_summary()

    def _on_hub_export_changed(self, path: str) -> None:
        self.export_path = path
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        count = len(self.source_paths)
        self.summary_sources.update(f"Sources: {count} file(s)")

        if self.export_path:
            self.summary_export.update(f"Export: {self.export_path}")
        else:
            self.summary_export.update("Export: default (source folder)")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "export_btn":
            self.compress_videos()

    def _get_output_directory(self) -> str:
        if self.export_path:
            return self.export_path
        if self.source_paths:
            return os.path.dirname(self.source_paths[0])
        return os.path.join(os.getcwd(), COMPRESSOR_OUTPUT_NAME)

    @work
    async def compress_videos(self) -> None:
        if not self.source_paths:
            self.show_status("⚠️ Add source files first in HUB", "warning")
            return

        out_format = self.format_select.value
        if out_format == Select.BLANK:
            out_format = "mp4"

        quality_key = self.quality_select.value
        if quality_key == Select.BLANK:
            quality_key = "balanced"

        crf = QUALITY_PROFILES.get(str(quality_key), 23)

        preset = self.preset_select.value
        if preset == Select.BLANK:
            preset = "medium"

        suffix = self.suffix_input.value.strip() or "_compressed"

        out_dir = self._get_output_directory()
        valid, error_msg = validate_output_path(out_dir)
        if not valid:
            self.show_status(f"❌ {error_msg}", "error")
            return

        if not ensure_output_dir(out_dir):
            self.show_status(f"❌ Could not create output directory: {out_dir}", "error")
            return

        total = len(self.source_paths)
        completed = 0
        failed = 0

        self.progress_bar.display = True
        self.progress_bar.update(total=total, progress=0)

        for idx, input_path in enumerate(self.source_paths, start=1):
            out_name = build_output_filename(
                input_path,
                suffix=suffix,
                extension=f".{out_format}",
            )
            out_path = os.path.join(out_dir, out_name)

            cmd = build_transcode_command(
                input_path=input_path,
                output_path=out_path,
                crf=crf,
                preset=str(preset),
            )

            self.progress_label.update(
                f"🔄 Processing {idx}/{total}: {os.path.basename(input_path)}"
            )
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
