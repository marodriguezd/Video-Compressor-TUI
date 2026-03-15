"""Compressor settings screen for batch conversion/compression with FFmpeg."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static, Label, ProgressBar, Input, Select, TabbedContent, TabPane
from textual import work
import os

from ui.components import ScreenBase
from logic import (
    run_ffmpeg_with_progress,
    get_video_duration,
    validate_output_path,
    ensure_output_dir,
    build_transcode_command,
    build_output_filename,
    COMPRESSOR_OUTPUT_NAME,
)


QUALITY_PROFILES = {
    # Community/common FFmpeg usage for H.264 (CRF method):
    # ~18-20 near-original, 23 default, 26+ smaller files.
    "highest": {"crf": 19, "audio_bitrate": "160k", "video_codec": "libx264"},
    "balanced": {"crf": 23, "audio_bitrate": "128k", "video_codec": "libx264"},
    "smaller": {"crf": 26, "audio_bitrate": "128k", "video_codec": "libx264"},
    "tiny": {"crf": 30, "audio_bitrate": "96k", "video_codec": "libx264"},
}


class CompressorScreen(ScreenBase):
    """Screen with compression settings and batch execution."""

    source_paths = tuple()
    export_path = ""

    CSS = (
        ScreenBase.CSS
        + """
    .screen-container {
        height: 1fr;
        padding: 1 2;
    }
    #compressor-scroll {
        height: 1fr;
    }
    #compressor-tabs {
        height: 1fr;
    }
    #compressor-tabs > TabPane {
        padding: 1;
        height: 1fr;
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
        min-height: 5;
    }
    .settings-grid Label {
        margin-bottom: 1;
        text-style: bold;
        color: $accent;
    }
    Select, Input {
        width: 1fr;
    }
    .run-controls {
        margin-top: 1;
        height: auto;
    }
    .run-controls > Button {
        width: 24;
        margin: 0;
    }
    .progress-section {
        dock: none;
        height: auto;
        min-height: 3;
        margin-top: 1;
    }
    """
    )

    def _compose_content(self) -> ComposeResult:
        with Vertical(classes="screen-container"):
            yield Static("🗜️ COMPRESSOR", classes="screen-title")

            with VerticalScroll(id="compressor-scroll"):
                with TabbedContent(initial="settings", id="compressor-tabs"):
                    with TabPane("🎛️ Settings", id="settings"):
                        with Vertical(classes="summary-box"):
                            self.summary_sources = Static("Sources: 0 files")
                            self.summary_export = Static("Export: default (source folder)")
                            yield self.summary_sources
                            yield self.summary_export

                        with Vertical(classes="settings-grid"):
                            with Vertical(classes="input-group"):
                                yield Label("Output format")
                                self.format_select = Select(
                                    [
                                        ("MP4 (recommended)", "mp4"),
                                        ("MKV", "mkv"),
                                        ("MOV", "mov"),
                                        ("WEBM", "webm"),
                                    ],
                                    value="mp4",
                                )
                                yield self.format_select

                            with Vertical(classes="input-group"):
                                yield Label("Quality profile")
                                self.quality_select = Select(
                                    [
                                        ("Highest quality (CRF 19)", "highest"),
                                        ("Balanced (CRF 23, default)", "balanced"),
                                        ("Smaller files (CRF 26)", "smaller"),
                                        ("Tiny files (CRF 30)", "tiny"),
                                    ],
                                    value="balanced",
                                )
                                yield self.quality_select

                            with Vertical(classes="input-group"):
                                yield Label("Encoding speed preset")
                                self.preset_select = Select(
                                    [
                                        ("fast", "fast"),
                                        ("medium (recommended)", "medium"),
                                        ("slow", "slow"),
                                    ],
                                    value="medium",
                                )
                                yield self.preset_select

                            with Vertical(classes="input-group"):
                                yield Label("Filename suffix")
                                self.suffix_input = Input(value="_compressed")
                                yield self.suffix_input

                    with TabPane("🚀 Run", id="run"):
                        with Vertical(classes="summary-box"):
                            self.run_sources = Static("Sources: 0 files")
                            self.run_export = Static("Export: default (source folder)")
                            self.run_profile = Static("Profile: balanced | format: mp4 | preset: medium")
                            yield self.run_sources
                            yield self.run_export
                            yield self.run_profile

                        with Horizontal(classes="run-controls"):
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

    def _selected_values(self) -> tuple[str, str, str]:
        out_format = self.format_select.value
        if out_format == Select.BLANK:
            out_format = "mp4"

        quality_key = self.quality_select.value
        if quality_key == Select.BLANK:
            quality_key = "balanced"

        preset = self.preset_select.value
        if preset == Select.BLANK:
            preset = "medium"

        return str(out_format), str(quality_key), str(preset)

    def _on_hub_sources_changed(self, paths: tuple) -> None:
        self.source_paths = paths
        self._refresh_summary()

    def _on_hub_export_changed(self, path: str) -> None:
        self.export_path = path
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        out_format, quality_key, preset = self._selected_values()
        count = len(self.source_paths)
        export = self.export_path or "default (source folder)"

        self.summary_sources.update(f"Sources: {count} file(s)")
        self.summary_export.update(f"Export: {export}")

        self.run_sources.update(f"Sources: {count} file(s)")
        self.run_export.update(f"Export: {export}")
        self.run_profile.update(
            f"Profile: {quality_key} | format: {out_format} | preset: {preset}"
        )

    def on_select_changed(self, _: Select.Changed) -> None:
        self._refresh_summary()

    def on_input_changed(self, _: Input.Changed) -> None:
        self._refresh_summary()

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

        out_format, quality_key, preset = self._selected_values()
        profile = QUALITY_PROFILES.get(quality_key, QUALITY_PROFILES["balanced"])
        crf = int(profile["crf"])
        video_codec = str(profile["video_codec"])
        audio_bitrate = str(profile["audio_bitrate"])
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
        not_smaller = 0

        self.progress_bar.display = True
        self.progress_bar.update(total=100, progress=0)

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
                preset=preset,
                video_codec=video_codec,
                audio_bitrate=audio_bitrate,
                emit_progress=True,
            )

            input_duration = await get_video_duration(input_path)

            def update_file_progress(ratio: float) -> None:
                global_ratio = ((idx - 1) + ratio) / total
                percent = int(max(0, min(100, global_ratio * 100)))
                self.progress_bar.update(progress=percent)
                self.progress_label.update(
                    f"🔄 {percent}% | {idx}/{total}: {os.path.basename(input_path)}"
                )

            self.progress_label.update(
                f"🔄 Processing {idx}/{total}: {os.path.basename(input_path)}"
            )
            success = await run_ffmpeg_with_progress(
                cmd,
                lambda _: None,
                update_file_progress,
                idx,
                out_path,
                input_duration,
            )

            if success:
                completed += 1
                if os.path.exists(input_path) and os.path.exists(out_path):
                    if os.path.getsize(out_path) >= os.path.getsize(input_path):
                        not_smaller += 1
            else:
                failed += 1

            self.progress_bar.update(progress=int((idx / total) * 100))

        self.progress_bar.display = False
        self.progress_label.update("")

        if failed == 0 and not_smaller == 0:
            self.show_status(f"✅ Done! {completed}/{total} file(s) processed", "success")
        elif failed == 0:
            self.show_status(
                f"✅ Done with notes: {completed}/{total} processed, {not_smaller} not smaller than source.",
                "warning",
            )
        else:
            self.show_status(
                f"⚠️ Finished with errors. Success: {completed}, Failed: {failed}, Not smaller: {not_smaller}",
                "warning",
            )
