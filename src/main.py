#!/usr/bin/env python3
"""
Video Compressor TUI - Unified entry point.

Usage:
    python src/main.py                       # Hub + compressor
    python src/main.py --tool compressor     # Open directly in Compressor
    python src/main.py --tool compressor --video video.mp4
"""

import argparse

from ui import VideoSliceApp


def parse_args():
    parser = argparse.ArgumentParser(
        description="Video Compressor TUI - Convert/compress media with FFmpeg"
    )
    parser.add_argument(
        "--tool",
        "-t",
        choices=["compressor"],
        help="Start directly in the compressor tool",
    )
    parser.add_argument("--video", "-v", help="Media file path to load on startup")
    return parser.parse_args()


def main():
    args = parse_args()

    tool = args.tool
    video_path = args.video

    if tool and video_path:
        app = VideoSliceApp(start_tab=tool, video_path=video_path)
    elif tool:
        app = VideoSliceApp(start_tab=tool)
    else:
        app = VideoSliceApp()

    app.run()


if __name__ == "__main__":
    main()
