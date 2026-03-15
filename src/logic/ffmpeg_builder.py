"""Utilities for building FFmpeg commands."""

import os


CLIPPER_OUTPUT_NAME = "clips_output"
SPLITTER_OUTPUT_NAME = "clips_output"
MERGER_OUTPUT_NAME = "merged_output"
COMPRESSOR_OUTPUT_NAME = "compressed_output"

SUPPORTED_MEDIA_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".m4v",
    ".webm",
    ".wmv",
    ".flv",
    ".mpeg",
    ".mpg",
    ".3gp",
    ".mp3",
    ".wav",
    ".flac",
    ".m4a",
    ".ogg",
    ".aac",
}


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


def build_transcode_command(
    input_path: str,
    output_path: str,
    crf: int = 23,
    preset: str = "medium",
    video_codec: str = "libx264",
    audio_bitrate: str = "128k",
    emit_progress: bool = False,
) -> list[str]:
    """Build FFmpeg command for re-encoding/compressing media."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-map",
        "0",
        "-c:v",
        video_codec,
        "-preset",
        preset,
        "-crf",
        str(crf),
        "-c:a",
        "aac",
        "-b:a",
        audio_bitrate,
    ]

    if emit_progress:
        cmd.extend(["-progress", "pipe:1", "-nostats"])

    cmd.append(output_path)
    return cmd


def build_output_filename(
    source_path: str, suffix: str = "_compressed", extension: str | None = None
) -> str:
    """Build output filename preserving base name and replacing extension."""
    stem, source_ext = os.path.splitext(os.path.basename(source_path))
    ext = extension or source_ext or ".mp4"
    if not ext.startswith("."):
        ext = f".{ext}"
    return f"{stem}{suffix}{ext}"


def is_supported_media_file(path: str) -> bool:
    """Return True if path has a supported media extension."""
    return os.path.splitext(path)[1].lower() in SUPPORTED_MEDIA_EXTENSIONS


def list_media_files_from_directory(directory: str, recursive: bool = True) -> list[str]:
    """List supported media files inside a directory."""
    if not os.path.isdir(directory):
        return []

    files: list[str] = []
    if recursive:
        for root, _, names in os.walk(directory):
            for name in names:
                path = os.path.join(root, name)
                if is_supported_media_file(path):
                    files.append(path)
    else:
        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if os.path.isfile(path) and is_supported_media_file(path):
                files.append(path)

    return sorted(files)
