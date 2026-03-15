"""Utilities for building FFmpeg commands."""

import os


CLIPPER_OUTPUT_NAME = "clips_output"
SPLITTER_OUTPUT_NAME = "clips_output"
MERGER_OUTPUT_NAME = "merged_output"


def build_cut_command(
    input_path: str, start: float, duration: float, output_path: str, reencode: bool
) -> list[str]:
    """Build FFmpeg command for cutting a video segment."""
    if reencode:
        return [
            "ffmpeg",
            "-y",
            "-ss",
            str(start),
            "-i",
            input_path,
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            output_path,
        ]
    else:
        return [
            "ffmpeg",
            "-y",
            "-ss",
            str(start),
            "-i",
            input_path,
            "-t",
            str(duration),
            "-c",
            "copy",
            output_path,
        ]


def build_concat_command(input_list_path: str, output_path: str) -> list[str]:
    """Build FFmpeg command for concatenating videos."""
    return [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        input_list_path,
        "-c",
        "copy",
        output_path,
    ]


def generate_clip_filename(
    idx: int,
    start: float,
    end: float,
    start_formatted: str,
    end_formatted: str,
    extension: str = ".mp4",
) -> str:
    """Generate a filename for a clip based on its index and time range."""
    return f"clip_{idx}_{start_formatted}_to_{end_formatted}{extension}"


def generate_default_output_path(source_path: str, folder_name: str) -> str:
    """Generate default output path for processed videos."""
    if source_path:
        video_dir = os.path.dirname(source_path) or os.getcwd()
    else:
        video_dir = os.getcwd()
    return os.path.join(video_dir, folder_name)
