"""Utilities for output path handling."""

import os


def get_default_output_path(source_path: str | None, folder_name: str) -> str:
    """Get the default output directory path based on source file location."""
    if source_path:
        video_dir = os.path.dirname(source_path) or os.getcwd()
    else:
        video_dir = os.getcwd()
    return os.path.join(video_dir, folder_name)


def get_output_directory(
    custom_path: str | None, source_path: str | None, folder_name: str
) -> str:
    """Get the output directory, either custom or default."""
    if custom_path:
        return custom_path
    return get_default_output_path(source_path, folder_name)


def validate_output_path(path: str) -> tuple[bool, str]:
    """Validate that the output path (or its nearest existing parent) is writable."""
    check = path
    while check and not os.path.exists(check):
        parent = os.path.dirname(check)
        if parent == check:
            break
        check = parent
    if check and os.path.exists(check):
        if not os.access(check, os.W_OK):
            return False, f"Folder is not writable: {check}"
        return True, ""
    return False, f"Cannot determine a writable location for: {path}"


def ensure_output_dir(path: str) -> bool:
    """Create output directory if it doesn't exist. Returns True on success."""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError:
        return False
