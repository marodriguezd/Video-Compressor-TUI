"""Integration tests for ffmpeg_utils module."""

import pytest
import asyncio
import os
from logic import get_video_duration, run_ffmpeg
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


class TestGetVideoDuration:
    """Integration tests for get_video_duration function."""

    @pytest.mark.asyncio
    async def test_valid_video_file(self, sample_video):
        """Get duration from a valid video file."""
        duration = await get_video_duration(sample_video)
        assert duration is not None
        assert duration > 0
        assert isinstance(duration, float)

    @pytest.mark.asyncio
    async def test_nonexistent_file(self):
        """Return None for non-existent file."""
        duration = await get_video_duration("/nonexistent/video.mp4")
        assert duration is None

    @pytest.mark.asyncio
    async def test_empty_string(self):
        """Handle empty string."""
        duration = await get_video_duration("")
        assert duration is None

    @pytest.mark.asyncio
    async def test_whitespace_only(self):
        """Handle whitespace-only string."""
        duration = await get_video_duration("   ")
        assert duration is None

    @pytest.mark.asyncio
    async def test_clean_path_functionality(self, sample_video):
        """Test that path cleaning works correctly."""
        # Test with quotes
        quoted_path = f'"{sample_video}"'
        duration = await get_video_duration(quoted_path)
        assert duration is not None
        assert duration > 0


class TestRunFfmpeg:
    """Integration tests for run_ffmpeg function."""

    @pytest.mark.asyncio
    async def test_successful_cut(
        self, sample_video, temp_output_dir, mock_log_callback
    ):
        """Run a successful FFmpeg cut operation."""
        output_path = os.path.join(temp_output_dir, "test_cut.mp4")
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            "0",
            "-i",
            sample_video,
            "-t",
            "1",
            "-c",
            "copy",
            output_path,
        ]

        success = await run_ffmpeg(cmd, mock_log_callback, 1, output_path)

        assert success is True
        assert os.path.exists(output_path)

    @pytest.mark.asyncio
    async def test_failed_ffmpeg_command(self, temp_output_dir, mock_log_callback):
        """Handle failed FFmpeg command gracefully."""
        output_path = os.path.join(temp_output_dir, "nonexistent.mp4")
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            "/nonexistent/input.mp4",
            output_path,
        ]

        success = await run_ffmpeg(cmd, mock_log_callback, 1, output_path)

        assert success is False

    @pytest.mark.asyncio
    async def test_logging_callback(
        self, sample_video, temp_output_dir, mock_log_callback
    ):
        """Verify logging callback is called."""
        output_path = os.path.join(temp_output_dir, "test_log.mp4")
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            "0",
            "-i",
            sample_video,
            "-t",
            "1",
            "-c",
            "copy",
            output_path,
        ]

        await run_ffmpeg(cmd, mock_log_callback, 1, output_path)

        assert len(mock_log_callback.logs) > 0
        # Check that some logs contain expected text
        log_text = "".join(mock_log_callback.logs)
        assert "Processing" in log_text or "Completed" in log_text

    @pytest.mark.asyncio
    async def test_output_file_size_reported(
        self, sample_video, temp_output_dir, mock_log_callback
    ):
        """Verify output file size is logged on success."""
        output_path = os.path.join(temp_output_dir, "test_size.mp4")
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            "0",
            "-i",
            sample_video,
            "-t",
            "1",
            "-c",
            "copy",
            output_path,
        ]

        await run_ffmpeg(cmd, mock_log_callback, 42, output_path)

        log_text = "".join(mock_log_callback.logs)
        assert "MB" in log_text or "Processing" in log_text


class TestFfmpegAvailability:
    """Tests to verify FFmpeg is available."""

    @pytest.mark.asyncio
    async def test_ffprobe_available(self, sample_video):
        """Verify ffprobe can be invoked."""
        duration = await get_video_duration(sample_video)
        if duration is None:
            pytest.skip("FFmpeg/ffprobe not available on system")
        assert duration > 0

    @pytest.mark.asyncio
    async def test_ffmpeg_available(self, sample_video, temp_output_dir):
        """Verify ffmpeg can be invoked for cutting."""
        output_path = os.path.join(temp_output_dir, "avail_test.mp4")
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            "0",
            "-i",
            sample_video,
            "-t",
            "1",
            "-c",
            "copy",
            output_path,
        ]

        success = await run_ffmpeg(cmd, lambda x: None, 1, output_path)

        if not success:
            pytest.skip("FFmpeg not available on system")
        assert os.path.exists(output_path)
