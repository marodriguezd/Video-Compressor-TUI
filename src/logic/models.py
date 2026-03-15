"""Data models for Video Slice TUI."""

import os


class Range:
    """Represents a time range for cutting/splitting."""

    def __init__(self, start_s: float, end_s: float, idx: int):
        if end_s <= start_s:
            raise ValueError("End must be after start")
        self.start = start_s
        self.end = end_s
        self.idx = idx

    def duration(self) -> float:
        return self.end - self.start
