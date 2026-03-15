"""Tests for ffmpeg_builder module."""

from logic import (
    build_cut_command,
    build_concat_command,
    generate_clip_filename,
    CLIPPER_OUTPUT_NAME,
    SPLITTER_OUTPUT_NAME,
    MERGER_OUTPUT_NAME,
    COMPRESSOR_OUTPUT_NAME,
    build_transcode_command,
    build_output_filename,
    is_supported_media_file,
    list_media_files_from_directory,
)


class TestBuildCutCommand:
    """Tests for build_cut_command function."""

    def test_reencode_true(self):
        """Build command with reencoding (slower, precise)."""
        cmd = build_cut_command(
            "/input/video.mp4", 10.0, 30.0, "/output/clip.mp4", reencode=True
        )

        assert cmd[0] == "ffmpeg"
        assert cmd[1] == "-y"
        assert cmd[2] == "-ss"
        assert cmd[3] == "10.0"
        assert cmd[4] == "-i"
        assert cmd[5] == "/input/video.mp4"
        assert cmd[6] == "-t"
        assert cmd[7] == "30.0"
        assert cmd[8] == "-c:v"
        assert cmd[9] == "libx264"
        assert cmd[10] == "-c:a"
        assert cmd[11] == "aac"
        assert cmd[12] == "/output/clip.mp4"

    def test_reencode_false(self):
        """Build command without reencoding (fast, stream copy)."""
        cmd = build_cut_command(
            "/input/video.mp4", 10.0, 30.0, "/output/clip.mp4", reencode=False
        )

        assert cmd[0] == "ffmpeg"
        assert cmd[1] == "-y"
        assert cmd[6] == "-t"
        assert cmd[7] == "30.0"
        assert cmd[8] == "-c"
        assert cmd[9] == "copy"
        # Should NOT have codec settings
        assert "-c:v" not in cmd
        assert "-c:a" not in cmd

    def test_windows_paths(self):
        """Build command with Windows paths."""
        cmd = build_cut_command(
            r"C:\Videos\input.mp4",
            0.0,
            60.0,
            r"C:\Output\clip.mp4",
            reencode=True,
        )

        assert cmd[5] == r"C:\Videos\input.mp4"
        assert cmd[12] == r"C:\Output\clip.mp4"

    def test_zero_start_time(self):
        """Build command with zero start time."""
        cmd = build_cut_command("/input.mp4", 0.0, 10.0, "/output.mp4", reencode=True)
        assert cmd[3] == "0.0"

    def test_float_values(self):
        """Build command with float values."""
        cmd = build_cut_command("/input.mp4", 5.5, 12.75, "/output.mp4", reencode=True)
        assert cmd[3] == "5.5"
        assert cmd[7] == "12.75"

    def test_long_duration(self):
        """Build command with long duration."""
        cmd = build_cut_command(
            "/input.mp4", 100.0, 3600.0, "/output.mp4", reencode=False
        )
        assert cmd[3] == "100.0"
        assert cmd[7] == "3600.0"


class TestBuildConcatCommand:
    """Tests for build_concat_command function."""

    def test_basic_concat(self):
        """Build basic concat command."""
        cmd = build_concat_command("/tmp/filelist.txt", "/output/merged.mp4")

        assert cmd[0] == "ffmpeg"
        assert cmd[1] == "-y"
        assert cmd[2] == "-f"
        assert cmd[3] == "concat"
        assert cmd[4] == "-safe"
        assert cmd[5] == "0"
        assert cmd[6] == "-i"
        assert cmd[7] == "/tmp/filelist.txt"
        assert cmd[8] == "-c"
        assert cmd[9] == "copy"
        assert cmd[10] == "/output/merged.mp4"

    def test_windows_paths(self):
        """Build concat command with Windows paths."""
        cmd = build_concat_command(r"C:\Temp\filelist.txt", r"C:\Output\merged.mp4")

        assert cmd[7] == r"C:\Temp\filelist.txt"
        assert cmd[10] == r"C:\Output\merged.mp4"

    def test_stream_copy_flag(self):
        """Verify stream copy flag is set."""
        cmd = build_concat_command("/list.txt", "/out.mp4")
        assert "-c" in cmd
        assert "copy" in cmd


class TestGenerateClipFilename:
    """Tests for generate_clip_filename function."""

    def test_basic_filename(self):
        """Generate basic clip filename."""
        filename = generate_clip_filename(1, 0.0, 30.0, "00-00-00", "00-00-30")
        assert filename == "clip_1_00-00-00_to_00-00-30.mp4"

    def test_high_index(self):
        """Generate filename with high index."""
        filename = generate_clip_filename(100, 600.0, 630.0, "00-10-00", "00-10-30")
        assert filename == "clip_100_00-10-00_to_00-10-30.mp4"

    def test_long_duration(self):
        """Generate filename for long duration clip."""
        filename = generate_clip_filename(5, 3600.0, 3700.0, "01-00-00", "01-01-40")
        assert filename == "clip_5_01-00-00_to_01-01-40.mp4"


class TestOutputConstants:
    """Tests for output folder name constants."""

    def test_clipper_output_name(self):
        """Verify clipper output folder name."""
        assert CLIPPER_OUTPUT_NAME == "clips_output"

    def test_splitter_output_name(self):
        """Verify splitter output folder name."""
        assert SPLITTER_OUTPUT_NAME == "clips_output"

    def test_merger_output_name(self):
        """Verify merger output folder name."""
        assert MERGER_OUTPUT_NAME == "merged_output"

    def test_constants_are_strings(self):
        """Verify constants are strings."""
        assert isinstance(CLIPPER_OUTPUT_NAME, str)
        assert isinstance(SPLITTER_OUTPUT_NAME, str)
        assert isinstance(MERGER_OUTPUT_NAME, str)

    def test_compressor_output_name(self):
        """Verify compressor output folder name."""
        assert COMPRESSOR_OUTPUT_NAME == "compressed_output"


class TestTranscodeBuilder:
    def test_transcode_command_has_compression_settings(self):
        cmd = build_transcode_command(
            "/input/video.mkv", "/output/video_compressed.mp4", crf=28, preset="fast"
        )

        assert cmd[0] == "ffmpeg"
        assert "-crf" in cmd
        assert "28" in cmd
        assert "-preset" in cmd
        assert "fast" in cmd
        assert "-c:v" in cmd
        assert "libx264" in cmd
        assert "-b:a" in cmd
        assert "128k" in cmd
        assert cmd[-1] == "/output/video_compressed.mp4"


    def test_transcode_command_default_common_values(self):
        cmd = build_transcode_command("/in.mp4", "/out.mp4")

        assert "-crf" in cmd
        assert "23" in cmd
        assert "-preset" in cmd
        assert "medium" in cmd

    def test_transcode_command_emit_progress(self):
        cmd = build_transcode_command("/in.mp4", "/out.mp4", emit_progress=True)
        assert "-progress" in cmd
        assert "pipe:1" in cmd
        assert "-nostats" in cmd

    def test_transcode_command_custom_codec_audio(self):
        cmd = build_transcode_command(
            "/in.mp4",
            "/out.mp4",
            crf=24,
            preset="medium",
            video_codec="libx264",
            audio_bitrate="128k",
        )

        assert "libx264" in cmd
        assert "128k" in cmd

    def test_output_filename_default_extension(self):
        assert build_output_filename("/tmp/video.mp4") == "video_compressed.mp4"

    def test_output_filename_custom_extension(self):
        assert (
            build_output_filename("/tmp/audio.mp3", suffix="_x", extension="mov")
            == "audio_x.mov"
        )

    def test_supported_file_detection(self):
        assert is_supported_media_file("clip.MKV") is True
        assert is_supported_media_file("notes.txt") is False

    def test_list_media_files_from_directory(self, tmp_path):
        media1 = tmp_path / "a.mp4"
        media1.write_text("x")
        media2 = tmp_path / "b.mp3"
        media2.write_text("x")
        junk = tmp_path / "c.txt"
        junk.write_text("x")

        files = list_media_files_from_directory(str(tmp_path), recursive=False)
        assert str(media1) in files
        assert str(media2) in files
        assert str(junk) not in files
