"""FFmpeg utility functions."""

import asyncio
import os


async def get_video_duration(path: str) -> float | None:
    """Get video duration using ffprobe."""
    clean_path = path.strip().strip('"').strip("'").strip()

    if not os.path.exists(clean_path):
        return None

    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            clean_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            duration_str = stdout.decode().strip()
            return float(duration_str)
        else:
            return None
    except Exception:
        return None


async def run_ffmpeg(cmd: list[str], log_callback, idx: int, out_path: str) -> bool:
    """Run ffmpeg command and log output."""
    try:
        log_callback(f"[Task #{idx}] ⏳ Processing... {os.path.basename(out_path)}\n")

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            log_callback(f"[Task #{idx}] ❌ FFmpeg Error\n")
            err = stderr.decode(errors="ignore")[:500]
            log_callback(f"{err}\n")
            return False
        else:
            file_size = os.path.getsize(out_path) / (1024 * 1024)
            log_callback(f"[Task #{idx}] ✅ Completed ({file_size:.1f} MB)\n")
            return True
    except Exception as exc:
        log_callback(f"[Task #{idx}] ❌ Exception: {exc}\n")
        return False
