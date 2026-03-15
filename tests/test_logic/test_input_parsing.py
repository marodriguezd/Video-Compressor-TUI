"""Tests for input_parsing module."""

import pytest
from logic import clean_pasted_path, clean_video_path


class TestCleanPastedPath:
    """Tests for clean_pasted_path function."""

    def test_no_change(self):
        """Path without any special characters."""
        assert clean_pasted_path("/path/to/file.mp4") == "/path/to/file.mp4"

    def test_strip_whitespace(self):
        """Strip leading and trailing whitespace."""
        assert clean_pasted_path("  /path/to/file.mp4  ") == "/path/to/file.mp4"

    def test_double_quotes(self):
        """Remove surrounding double quotes."""
        assert clean_pasted_path('"/path/to/file.mp4"') == "/path/to/file.mp4"

    def test_single_quotes(self):
        """Remove surrounding single quotes."""
        assert clean_pasted_path("'/path/to/file.mp4'") == "/path/to/file.mp4"

    def test_powershell_prefix(self):
        """Remove PowerShell & prefix."""
        result = clean_pasted_path('& "C:\\Path\\To\\File.mp4"')
        assert result == "C:\\Path\\To\\File.mp4"

    def test_powershell_prefix_no_quotes(self):
        """Remove PowerShell & prefix without quotes."""
        result = clean_pasted_path("& /path/to/file.mp4")
        assert result == "/path/to/file.mp4"

    def test_windows_path_with_quotes(self):
        """Clean Windows path with quotes."""
        result = clean_pasted_path('"C:\\Users\\Test\\video.mp4"')
        assert result == "C:\\Users\\Test\\video.mp4"

    def test_empty_string(self):
        """Handle empty string."""
        assert clean_pasted_path("") == ""

    def test_only_whitespace(self):
        """Handle string with only whitespace."""
        assert clean_pasted_path("   ") == ""

    def test_multiple_quotes_stripped(self):
        """Ensure only outer quotes are removed."""
        assert clean_pasted_path('"file.mp4"') == "file.mp4"
        assert clean_pasted_path("'file.mp4'") == "file.mp4"

    def test_whitespace_inside_quotes_preserved(self):
        """Preserve whitespace inside quotes."""
        result = clean_pasted_path('"file with spaces.mp4"')
        assert result == "file with spaces.mp4"


class TestCleanVideoPath:
    """Tests for clean_video_path function."""

    def test_basic_clean(self):
        """Basic path cleaning."""
        assert clean_video_path("  /path/to/video.mp4  ") == "/path/to/video.mp4"

    def test_with_powershell_prefix(self):
        """Clean path with PowerShell prefix."""
        result = clean_video_path('& "C:\\Videos\\movie.mp4"')
        assert result == "C:\\Videos\\movie.mp4"

    def test_with_quotes(self):
        """Clean path with quotes."""
        result = clean_video_path("'/home/user/video.mp4'")
        assert result == "/home/user/video.mp4"

    def test_empty_path(self):
        """Handle empty path."""
        assert clean_video_path("") == ""

    def test_complex_powershell_command(self):
        """Clean complex PowerShell command."""
        result = clean_video_path('& "C:\\My Videos\\test video.mp4"')
        assert result == "C:\\My Videos\\test video.mp4"

    def test_already_clean_path(self):
        """Already clean path should remain unchanged."""
        assert clean_video_path("/clean/path/video.mp4") == "/clean/path/video.mp4"
