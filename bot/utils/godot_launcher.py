"""
Utility to launch Godot project locally.
"""

import logging
import os
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


def _resolve_executable(explicit_path: Optional[str]) -> str:
    if explicit_path:
        return explicit_path
    # Common fallbacks
    return "godot4"


def launch_godot_project(executable_path: Optional[str], project_dir: str) -> bool:
    """Launch Godot on the given project directory. Returns True if started."""
    exe = _resolve_executable(executable_path)
    try:
        # Godot 4: launch the game (not editor) with --path
        cmd = [exe, "--path", project_dir]
        logger.info(f"Launching Godot: {' '.join(cmd)}")
        # Detached startup, without blocking the bot
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except FileNotFoundError:
        logger.error("Godot not found. Set GODOT_EXECUTABLE_PATH in .env (ex: C:/Program Files/Godot/Godot_v4.4/godot4.exe).")
        return False
    except Exception as exc:
        logger.error(f"Godot launch failed: {exc}")
        return False


def export_godot_project(
    executable_path: Optional[str],
    project_dir: str,
    preset: str,
    export_path: str,
) -> bool:
    """Export Godot project in headless mode for a given preset."""
    exe = _resolve_executable(executable_path)
    try:
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        cmd = [
            exe,
            "--headless",
            "--path",
            project_dir,
            "--export-release",
            preset,
            export_path,
        ]
        logger.info(f"Export Godot: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        return True
    except FileNotFoundError:
        logger.error("Godot not found. Set GODOT_EXECUTABLE_PATH in .env (ex: C:/Program Files/Godot/Godot_v4.4/godot4.exe).")
        return False
    except subprocess.CalledProcessError as exc:
        logger.error(f"Godot export failed (code {exc.returncode}).")
        return False
    except Exception as exc:
        logger.error(f"Godot export failed: {exc}")
        return False
