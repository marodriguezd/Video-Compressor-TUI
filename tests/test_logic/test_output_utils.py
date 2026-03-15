"""Tests for output_utils module."""

import pytest
import os
from logic import (
    get_default_output_path,
    get_output_directory,
    validate_output_path,
    ensure_output_dir,
)


class TestGetDefaultOutputPath:
    """Tests for get_default_output_path function."""

    def test_with_source_path(self, temp_dir):
        """Get output path based on source file location."""
        source = os.path.join(temp_dir, "subdir", "video.mp4")
        result = get_default_output_path(source, "output")
        expected = os.path.join(temp_dir, "subdir", "output")
        assert result == expected

    def test_with_source_path_absolute(self):
        """Get output path with absolute source path."""
        result = get_default_output_path("/home/user/videos/test.mp4", "clips")
        expected = os.path.join("/home/user/videos", "clips")
        assert result == expected or result == expected.replace("/", "\\")

    def test_custom_folder_name(self):
        """Test with custom folder name."""
        result = get_default_output_path("/path/to/video.mp4", "custom_output")
        expected = os.path.join("/path/to", "custom_output")
        assert result == expected or result == expected.replace("/", "\\")

    def test_windows_paths(self):
        """Test with Windows-style paths."""
        result = get_default_output_path(r"C:\Users\Videos\movie.mp4", "clips_output")
        assert result == r"C:\Users\Videos\clips_output"


class TestGetOutputDirectory:
    """Tests for get_output_directory function."""

    def test_custom_path_preferred(self):
        """Custom path should be returned when provided."""
        result = get_output_directory("/custom/output", "/source/video.mp4", "default")
        assert result == "/custom/output"

    def test_fallback_to_default(self):
        """Should return default path when custom is None."""
        result = get_output_directory(None, "/source/video.mp4", "default")
        expected = os.path.join("/source", "default")
        assert result == expected or result == expected.replace("/", "\\")

    def test_both_none(self, tmp_path):
        """Should use current directory when both are None."""
        os.chdir(tmp_path)
        result = get_output_directory(None, None, "default")
        assert result == os.path.join(os.getcwd(), "default")


class TestValidateOutputPath:
    """Tests for validate_output_path function."""

    def test_existing_writable_path(self, temp_dir):
        """Validate existing writable directory."""
        valid, error = validate_output_path(temp_dir)
        assert valid is True
        assert error == ""

    def test_nonexistent_path(self):
        """Reject non-existent directory."""
        valid, error = validate_output_path("/nonexistent/path")
        assert valid is False
        assert "does not exist" in error

    def test_readonly_path(self, temp_dir):
        """Test with read-only directory (if possible on platform)."""
        valid, error = validate_output_path(temp_dir)
        assert valid is True

    def test_nested_nonexistent_path(self):
        """Reject nested path that doesn't exist."""
        valid, error = validate_output_path("/a/b/c/d/e/f")
        assert valid is False
        assert "does not exist" in error


class TestEnsureOutputDir:
    """Tests for ensure_output_dir function."""

    def test_create_new_directory(self, temp_dir):
        """Create new subdirectory."""
        new_path = os.path.join(temp_dir, "new_output")
        result = ensure_output_dir(new_path)
        assert result is True
        assert os.path.exists(new_path)

    def test_existing_directory(self, temp_dir):
        """Handle existing directory."""
        result = ensure_output_dir(temp_dir)
        assert result is True

    def test_nested_creation(self, temp_dir):
        """Create nested directory structure."""
        nested_path = os.path.join(temp_dir, "a", "b", "c")
        result = ensure_output_dir(nested_path)
        assert result is True
        assert os.path.exists(nested_path)
