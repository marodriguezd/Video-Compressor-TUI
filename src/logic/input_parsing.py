"""Utilities for parsing and cleaning user input."""

import re


def clean_pasted_path(path: str) -> str:
    """Clean a path string that might have been pasted from a terminal/shell."""
    if not path:
        return ""

    path = path.strip()

    if path.startswith("&"):
        path = path[1:].strip()

    if (path.startswith('"') and path.endswith('"')) or (
        path.startswith("'") and path.endswith("'")
    ):
        path = path[1:-1]

    path = path.strip()

    return path


def clean_video_path(path: str) -> str:
    """Clean video path string for consistent use."""
    path = clean_pasted_path(path)
    return path.strip()
