"""Reusable file dialog component."""

import tkinter as tk
from tkinter import filedialog


def open_file_dialog(multi: bool = False, title: str = "Select a video"):
    """Open a file dialog and return selected path(s)."""
    root = tk.Tk()
    root.withdraw()

    if multi:
        file_paths = filedialog.askopenfilenames(
            title=title,
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.m4v"),
                ("Audio files", "*.mp3 *.wav *.flac *.m4a *.ogg"),
                ("All files", "*.*"),
            ],
        )
        root.destroy()
        return file_paths if file_paths else None
    else:
        file_path = filedialog.askopenfilename(
            title=title,
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.m4v"),
                ("Audio files", "*.mp3 *.wav *.flac *.m4a *.ogg"),
                ("All files", "*.*"),
            ],
        )
        root.destroy()
        return file_path if file_path else None
