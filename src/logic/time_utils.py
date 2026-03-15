"""Time parsing and formatting utilities."""

from datetime import timedelta


def parse_time(s: str) -> float:
    """Parse a time string into seconds.

    Accepts HH:MM:SS, MM:SS, SS, or decimal hours (e.g. 3.5 -> 3h30m).
    """
    s = s.strip()
    if not s:
        raise ValueError("Empty time")

    if s.replace(".", "", 1).replace("-", "", 1).isdigit() and ":" not in s:
        if "." in s:
            hours = float(s)
            return hours * 3600.0
        else:
            return float(s)

    parts = s.split(":")
    parts = [p for p in parts if p != ""]

    if len(parts) == 1:
        return float(parts[0])
    elif len(parts) == 2:
        minutes = float(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError(f"Can't parse time: {s}")


def format_hhmmss(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    td = timedelta(seconds=int(seconds))
    total_seconds = int(td.total_seconds())
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60

    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    else:
        return f"{m:02d}:{s:02d}"
