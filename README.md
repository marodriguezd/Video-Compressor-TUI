# Video Compressor TUI

`Video Compressor TUI` is a terminal UI (Textual) focused on **batch video/audio compression and conversion** powered by FFmpeg.

## What this first design includes

## Scope

This project is now focused only on **compression/conversion batch workflows**. Legacy tools (clipper, splitter, merger) were removed from the app UI to keep a single-purpose product.


- HUB tab for source management: add files/folder, include subfolders, review queue, remove entries.
- HUB tab for export route selection (or default to first source folder).
- Conversion between many media extensions (for example: `mkv -> mp4`, `mp3 -> mov`).
- Compressor tab focused on settings + execution:
  - Output format selector
  - Quality profile selector (maps to CRF presets)
  - Encoding speed preset selector
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


### Default compression profile policy

The app defaults to **Balanced (CRF 23, H.264, preset medium)**, which matches common FFmpeg community usage for good quality/size tradeoff.

Other presets follow common CRF ranges:
- Highest quality: CRF 19
- Smaller files: CRF 26
- Tiny files: CRF 30

> Note: output size can still vary depending on source complexity.
