"""
Utilitaire pour lancer le projet Godot localement.
"""

import logging
import os
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


def _resolve_executable(explicit_path: Optional[str]) -> str:
    if explicit_path:
        return explicit_path
    # Fallbacks courants
    return "godot4"


def launch_godot_project(executable_path: Optional[str], project_dir: str) -> bool:
    """Lance Godot sur le répertoire de projet donné. Retourne True si démarré."""
    exe = _resolve_executable(executable_path)
    try:
        # Godot 4: lancer le jeu (pas l'éditeur) avec --path
        cmd = [exe, "--path", project_dir]
        logger.info(f"Lancement de Godot: {' '.join(cmd)}")
        # Démarrage détaché, sans bloquer le bot
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except FileNotFoundError:
        logger.error("Godot introuvable. Définissez GODOT_EXECUTABLE_PATH dans .env (ex: C:/Program Files/Godot/Godot_v4.4/godot4.exe).")
        return False
    except Exception as exc:
        logger.error(f"Échec du lancement Godot: {exc}")
        return False


def export_godot_project(
    executable_path: Optional[str],
    project_dir: str,
    preset: str,
    export_path: str,
) -> bool:
    """Exporte le projet Godot en mode headless pour un preset donné."""
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
        logger.error("Godot introuvable. Définissez GODOT_EXECUTABLE_PATH dans .env (ex: C:/Program Files/Godot/Godot_v4.4/godot4.exe).")
        return False
    except subprocess.CalledProcessError as exc:
        logger.error(f"Échec export Godot (code {exc.returncode}).")
        return False
    except Exception as exc:
        logger.error(f"Échec export Godot: {exc}")
        return False
