"""End-to-end CLI tests."""

import pytest
import subprocess
import sys
import os


# Go up 3 levels: tests/test_e2e/test_cli.py -> tests -> project_root
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")


class TestPythonSyntax:
    """Tests to verify all Python files have valid syntax."""

    def test_main_syntax(self):
        """Verify main.py has valid syntax."""
        main_py = os.path.join(PROJECT_ROOT, "src", "main.py")
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", main_py],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_all_ui_files_syntax(self):
        """Verify all UI files have valid syntax."""
        ui_files = [
            os.path.join(SRC_DIR, "ui", "app.py"),
            os.path.join(SRC_DIR, "ui", "screens", "hub_screen.py"),
            os.path.join(SRC_DIR, "ui", "screens", "compressor_screen.py"),
            os.path.join(SRC_DIR, "ui", "components", "base_screen.py"),
            os.path.join(SRC_DIR, "ui", "components", "file_dialog.py"),
            os.path.join(SRC_DIR, "ui", "components", "logger.py"),
        ]

        for filepath in ui_files:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", filepath],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Syntax error in {filepath}"

    def test_all_logic_files_syntax(self):
        """Verify all logic files have valid syntax."""
        logic_files = [
            os.path.join(SRC_DIR, "logic", "__init__.py"),
            os.path.join(SRC_DIR, "logic", "models.py"),
            os.path.join(SRC_DIR, "logic", "time_utils.py"),
            os.path.join(SRC_DIR, "logic", "ffmpeg_utils.py"),
            os.path.join(SRC_DIR, "logic", "input_parsing.py"),
            os.path.join(SRC_DIR, "logic", "output_utils.py"),
            os.path.join(SRC_DIR, "logic", "ffmpeg_builder.py"),
        ]

        for filepath in logic_files:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", filepath],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Syntax error in {filepath}"


class TestImports:
    """Tests to verify imports work correctly."""

    def test_logic_imports(self):
        """Verify all logic module imports work."""
        env = os.environ.copy()
        env["PYTHONPATH"] = SRC_DIR
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from logic import parse_time, format_hhmmss, get_video_duration, run_ffmpeg, clean_video_path, Range, get_default_output_path, build_cut_command",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, result.stderr

    def test_ui_imports(self):
        """Verify UI imports work."""
        env = os.environ.copy()
        env["PYTHONPATH"] = SRC_DIR
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from ui.screens.compressor_screen import CompressorScreen",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, result.stderr
