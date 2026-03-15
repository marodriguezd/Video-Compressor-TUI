"""Logic module exports."""

from .time_utils import parse_time, format_hhmmss
from .ffmpeg_utils import get_video_duration, run_ffmpeg
from .input_parsing import clean_video_path, clean_pasted_path
from .models import Range
from .output_utils import (
    get_default_output_path,
    get_output_directory,
    validate_output_path,
    ensure_output_dir,
)
from .ffmpeg_builder import (
    build_cut_command,
    build_concat_command,
    build_transcode_command,
    build_output_filename,
    is_supported_media_file,
    list_media_files_from_directory,
    generate_clip_filename,
    CLIPPER_OUTPUT_NAME,
    SPLITTER_OUTPUT_NAME,
    MERGER_OUTPUT_NAME,
    COMPRESSOR_OUTPUT_NAME,
)

__all__ = [
    "parse_time",
    "format_hhmmss",
    "get_video_duration",
    "run_ffmpeg",
    "clean_video_path",
    "clean_pasted_path",
    "Range",
    "get_default_output_path",
    "get_output_directory",
    "validate_output_path",
    "ensure_output_dir",
    "build_cut_command",
    "build_concat_command",
    "build_transcode_command",
    "build_output_filename",
    "is_supported_media_file",
    "list_media_files_from_directory",
    "generate_clip_filename",
    "CLIPPER_OUTPUT_NAME",
    "SPLITTER_OUTPUT_NAME",
    "MERGER_OUTPUT_NAME",
    "COMPRESSOR_OUTPUT_NAME",
]
