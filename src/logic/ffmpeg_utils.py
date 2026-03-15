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
        stdout, _ = await proc.communicate()

        if proc.returncode == 0:
            duration_str = stdout.decode().strip()
            return float(duration_str)
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
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            log_callback(f"[Task #{idx}] ❌ FFmpeg Error\n")
            err = stderr.decode(errors="ignore")[:500]
            log_callback(f"{err}\n")
            return False

        file_size = os.path.getsize(out_path) / (1024 * 1024)
        log_callback(f"[Task #{idx}] ✅ Completed ({file_size:.1f} MB)\n")
        return True
    except Exception as exc:
        log_callback(f"[Task #{idx}] ❌ Exception: {exc}\n")
        return False


async def run_ffmpeg_with_progress(
    cmd: list[str],
    log_callback,
    progress_callback,
    idx: int,
    out_path: str,
    total_duration: float | None,
) -> bool:
    """Run ffmpeg and stream progress ratio (0..1) when available."""
    try:
        log_callback(f"[Task #{idx}] ⏳ Processing... {os.path.basename(out_path)}\n")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stderr_chunks: list[str] = []

        async def _read_stdout_progress():
            if not proc.stdout:
                return
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode(errors="ignore").strip()
                if text.startswith("out_time_ms=") and total_duration and total_duration > 0:
                    try:
                        out_time_ms = int(text.split("=", 1)[1])
                        elapsed_s = out_time_ms / 1_000_000
                        ratio = max(0.0, min(1.0, elapsed_s / total_duration))
                        progress_callback(ratio)
                    except Exception:
                        pass

        async def _read_stderr():
            if not proc.stderr:
                return
            while True:
                line = await proc.stderr.readline()
                if not line:
                    break
                if len(stderr_chunks) < 50:
                    stderr_chunks.append(line.decode(errors="ignore"))

        await asyncio.gather(_read_stdout_progress(), _read_stderr())
        return_code = await proc.wait()

        if return_code != 0:
            log_callback(f"[Task #{idx}] ❌ FFmpeg Error\n")
            err = "".join(stderr_chunks)[:500]
            log_callback(f"{err}\n")
            return False

        progress_callback(1.0)
        file_size = os.path.getsize(out_path) / (1024 * 1024)
        log_callback(f"[Task #{idx}] ✅ Completed ({file_size:.1f} MB)\n")
        return True
    except Exception as exc:
        log_callback(f"[Task #{idx}] ❌ Exception: {exc}\n")
        return False
