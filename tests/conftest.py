"""Pytest configuration and fixtures for Video-Slice-TUI tests."""

import pytest
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Default test video path (adjust for your system)
DEFAULT_VIDEO_PATH = r"C:\Users\marod\Videos\2025-12-17 00-00-10.mp4"


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_video: marks tests that require a real video file"
    )


@pytest.fixture(scope="session")
def video_path():
    """Path to a test video file. Skip if not found."""
    path = os.environ.get("TEST_VIDEO_PATH", DEFAULT_VIDEO_PATH)
    if not os.path.exists(path):
        pytest.skip(f"Test video not found: {path}")
    return path


@pytest.fixture
def sample_video(video_path):
    """Return the video path if it exists."""
    return video_path


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test outputs."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return str(output_dir)


@pytest.fixture
def temp_output_dir(temp_dir):
    """Provide a temporary output directory."""
    return temp_dir


@pytest.fixture
def mock_log_callback():
    """Provide a mock log callback for FFmpeg operations."""
    logs = []

    def callback(text):
        logs.append(text)

    callback.logs = logs
    return callback
