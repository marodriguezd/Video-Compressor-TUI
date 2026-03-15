"""Tests for time_utils module."""

import pytest
from logic import parse_time, format_hhmmss


class TestParseTime:
    """Tests for parse_time function."""

    def test_hhmmss_format(self):
        """Parse standard HH:MM:SS format."""
        assert parse_time("01:30:45") == 5445.0

    def test_hhmmss_single_digit_hours(self):
        """Parse HH:MM:SS with single digit hours."""
        assert parse_time("0:05:30") == 330.0

    def test_mm_ss_format(self):
        """Parse MM:SS format."""
        assert parse_time("30:45") == 1845.0

    def test_mm_ss_single_digit(self):
        """Parse MM:SS with single digit values."""
        assert parse_time("5:30") == 330.0

    def test_ss_format(self):
        """Parse seconds only."""
        assert parse_time("45") == 45.0

    def test_decimal_hours(self):
        """Parse decimal hours (e.g., 1.5 = 1 hour 30 minutes)."""
        assert parse_time("1.5") == 5400.0
        assert parse_time("0.5") == 1800.0

    def test_decimal_hours_large(self):
        """Parse decimal hours with larger values."""
        assert parse_time("2.25") == 8100.0

    def test_zero(self):
        """Parse zero."""
        assert parse_time("0") == 0.0

    def test_whitespace_handling(self):
        """Parse time with extra whitespace."""
        assert parse_time("  01:30:45  ") == 5445.0

    def test_invalid_string(self):
        """Raise error for invalid time string."""
        with pytest.raises(ValueError):
            parse_time("invalid")

    def test_empty_string(self):
        """Raise error for empty string."""
        with pytest.raises(ValueError):
            parse_time("")

    def test_too_many_colons(self):
        """Raise error for too many colons."""
        with pytest.raises(ValueError):
            parse_time("01:30:45:00")

    def test_negative_number(self):
        """Parse negative number (should work)."""
        assert parse_time("-10") == -10.0


class TestFormatHhmmss:
    """Tests for format_hhmmss function."""

    def test_with_hours(self):
        """Format time with hours."""
        assert format_hhmmss(5445.0) == "01:30:45"

    def test_without_hours(self):
        """Format time without hours (less than 1 hour)."""
        assert format_hhmmss(1845.0) == "30:45"

    def test_single_digits(self):
        """Format time with single digit values."""
        assert format_hhmmss(65.0) == "01:05"

    def test_zero(self):
        """Format zero."""
        assert format_hhmmss(0.0) == "00:00"

    def test_exactly_one_hour(self):
        """Format exactly one hour."""
        assert format_hhmmss(3600.0) == "01:00:00"

    def test_less_than_minute(self):
        """Format less than a minute."""
        assert format_hhmmss(45.0) == "00:45"

    def test_large_value(self):
        """Format large time value."""
        assert format_hhmmss(3661.0) == "01:01:01"

    def test_fractional_seconds_rounded_down(self):
        """Test that fractional seconds are truncated."""
        assert format_hhmmss(90.5) == "01:30"
