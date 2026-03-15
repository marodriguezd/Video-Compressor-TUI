"""Tests for models module."""

import pytest
from logic import Range


class TestRange:
    """Tests for Range class."""

    def test_basic_creation(self):
        """Create a basic range."""
        r = Range(0.0, 30.0, 1)
        assert r.start == 0.0
        assert r.end == 30.0
        assert r.idx == 1

    def test_duration_calculation(self):
        """Calculate duration correctly."""
        r = Range(10.0, 60.0, 1)
        assert r.duration() == 50.0

    def test_duration_with_floats(self):
        """Calculate duration with float values."""
        r = Range(5.5, 35.75, 1)
        assert r.duration() == 30.25

    def test_negative_duration_raises_error(self):
        """End before start should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Range(60.0, 30.0, 1)
        assert "End must be after start" in str(exc_info.value)

    def test_equal_start_end_raises_error(self):
        """Start equals end should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Range(30.0, 30.0, 1)
        assert "End must be after start" in str(exc_info.value)

    def test_large_values(self):
        """Handle large time values."""
        r = Range(3600.0, 7200.0, 1)
        assert r.duration() == 3600.0

    def test_small_values(self):
        """Handle small time values."""
        r = Range(0.1, 0.5, 1)
        assert r.duration() == 0.4

    def test_zero_start(self):
        """Handle zero start time."""
        r = Range(0.0, 10.0, 1)
        assert r.start == 0.0
        assert r.duration() == 10.0

    def test_custom_index(self):
        """Use custom index values."""
        r = Range(0.0, 10.0, 42)
        assert r.idx == 42

    def test_negative_times(self):
        """Handle negative times (edge case)."""
        r = Range(-10.0, 0.0, 1)
        assert r.duration() == 10.0

    def test_attributes_are_floats(self):
        """Verify attributes are float type."""
        r = Range(1.0, 2.0, 1)
        assert isinstance(r.start, float)
        assert isinstance(r.end, float)
        assert isinstance(r.idx, int)
