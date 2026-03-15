"""Integration tests for video processing workflows."""

import pytest
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from logic import (
    build_cut_command,
    build_concat_command,
    ensure_output_dir,
    clean_video_path,
)


class TestClipperWorkflow:
    """Integration tests for clipper workflow."""

    def test_single_clip_creation(self, sample_video, temp_output_dir):
        """Test creating a single clip from video."""
        output_path = os.path.join(temp_output_dir, "single_clip.mp4")

        cmd = build_cut_command(sample_video, 0.0, 5.0, output_path, reencode=False)

        assert cmd[0] == "ffmpeg"
        assert "-i" in cmd
        assert sample_video in cmd
        assert output_path in cmd

        assert ensure_output_dir(temp_output_dir)

    def test_multiple_clips_commands(self, sample_video, temp_output_dir):
        """Test generating commands for multiple clips."""
        ranges = [
            (0.0, 10.0),
            (10.0, 20.0),
            (20.0, 30.0),
        ]

        commands = []
        for i, (start, end) in enumerate(ranges, 1):
            output_path = os.path.join(temp_output_dir, f"clip_{i}.mp4")
            cmd = build_cut_command(
                sample_video, start, end - start, output_path, reencode=False
            )
            commands.append((cmd, output_path))

        assert len(commands) == 3

        for cmd, output_path in commands:
            assert os.path.dirname(output_path) == temp_output_dir
            assert cmd[0] == "ffmpeg"
            assert "-c" in cmd
            assert "copy" in cmd

    def test_precise_cut_with_reencode(self, sample_video, temp_output_dir):
        """Test precise cut with reencoding."""
        output_path = os.path.join(temp_output_dir, "precise_clip.mp4")

        cmd = build_cut_command(sample_video, 5.5, 15.5, output_path, reencode=True)

        assert "-c:v" in cmd
        assert "libx264" in cmd
        assert "-c:a" in cmd
        assert "aac" in cmd


class TestSplitterWorkflow:
    """Integration tests for splitter workflow."""

    def test_equal_chunk_commands(self, sample_video, temp_output_dir):
        """Test generating commands for equal-sized chunks."""
        chunk_duration = 60.0  # 1 minute chunks
        video_duration = 180.0  # 3 minute video

        ranges = []
        start = 0.0
        while start < video_duration:
            end = min(start + chunk_duration, video_duration)
            ranges.append((start, end))
            start = end

        assert len(ranges) == 3

        for i, (start, end) in enumerate(ranges, 1):
            output_path = os.path.join(temp_output_dir, f"chunk_{i}.mp4")
            cmd = build_cut_command(
                sample_video, start, end - start, output_path, reencode=False
            )

            assert cmd[0] == "ffmpeg"
            assert float(cmd[3]) == start

    def test_small_chunk_size(self, sample_video, temp_output_dir):
        """Test with small chunk size."""
        chunk_duration = 10.0
        video_duration = 25.0

        ranges = []
        start = 0.0
        while start < video_duration:
            end = min(start + chunk_duration, video_duration)
            ranges.append((start, end))
            start = end

        # Should create 3 chunks: 0-10, 10-20, 20-25
        assert len(ranges) == 3
        assert ranges[0] == (0.0, 10.0)
        assert ranges[1] == (10.0, 20.0)
        assert ranges[2] == (20.0, 25.0)


class TestMergerWorkflow:
    """Integration tests for merger workflow."""

    def test_concat_file_creation(self, temp_output_dir):
        """Test creating concat file content."""
        video_files = [
            "/path/to/video1.mp4",
            "/path/to/video2.mp4",
            "/path/to/video3.mp4",
        ]

        list_path = os.path.join(temp_output_dir, "filelist.txt")

        with open(list_path, "w") as f:
            for video_path in video_files:
                f.write(f"file '{video_path}'\n")

        assert os.path.exists(list_path)

        with open(list_path, "r") as f:
            content = f.read()

        assert "file '/path/to/video1.mp4'" in content
        assert "file '/path/to/video2.mp4'" in content
        assert "file '/path/to/video3.mp4'" in content

    def test_concat_command_structure(self, temp_output_dir):
        """Test concat command structure."""
        list_path = os.path.join(temp_output_dir, "filelist.txt")
        output_path = os.path.join(temp_output_dir, "merged.mp4")

        cmd = build_concat_command(list_path, output_path)

        assert cmd[0] == "ffmpeg"
        assert "-f" in cmd
        assert "concat" in cmd
        assert "-safe" in cmd
        assert "0" in cmd
        assert list_path in cmd
        assert "-c" in cmd
        assert "copy" in cmd


class TestPathHandling:
    """Tests for path handling in workflows."""

    def test_clean_video_path(self):
        """Test path cleaning for workflows."""
        paths = [
            '  "C:\\Videos\\movie.mp4"  ',
            "& 'C:\\Videos\\movie.mp4'",
            "C:\\Videos\\movie.mp4",
        ]

        for path in paths:
            cleaned = clean_video_path(path)
            assert cleaned.endswith(".mp4")
            assert not cleaned.startswith(" ")
            if "&" in path:
                assert "&" not in cleaned

    def test_output_directory_creation(self, temp_output_dir):
        """Test creating output directories for different tools."""
        tools = ["clips_output", "merged_output"]

        for tool_folder in tools:
            output_path = os.path.join(temp_output_dir, tool_folder, "subdir")
            assert ensure_output_dir(output_path)
            assert os.path.exists(output_path)
