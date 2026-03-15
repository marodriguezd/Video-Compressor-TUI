# Video Compressor TUI

`Video Compressor TUI` is a terminal UI (Textual) focused on **batch video/audio compression and conversion** powered by FFmpeg.

## What this first design includes

## Scope

This project is now focused only on **compression/conversion batch workflows**. Legacy tools (clipper, splitter, merger) were removed from the app UI to keep a single-purpose product.


- Batch queue: add many files manually.
- Bulk import from a folder (with optional recursive scan).
- Conversion between many media extensions (for example: `mkv -> mp4`, `mp3 -> mov`).
- Compression controls for:
  - Output format
  - CRF
  - Preset
  - Output filename suffix (`_compressed` by default)
- Default output route behavior:
  - Uses the same source folder by default.
  - Supports custom output folder selection.

## Supported input discovery extensions

- Video: `.mp4`, `.mkv`, `.avi`, `.mov`, `.m4v`, `.webm`, `.wmv`, `.flv`, `.mpeg`, `.mpg`, `.3gp`
- Audio: `.mp3`, `.wav`, `.flac`, `.m4a`, `.ogg`, `.aac`

## Run

```bash
PYTHONPATH=src python -m main
```

> FFmpeg / FFprobe must be available in your system PATH.
