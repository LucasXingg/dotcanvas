"""Utilities for installing Python packages at runtime for canvas views."""

from __future__ import annotations

import importlib
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable

logger = logging.getLogger("dot.canvas")

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DEF_USER_SITE = _PROJECT_ROOT / "user_site"
_MANIFEST_FILENAME = "__dotcanvas_installed__.json"


def _resolve_user_site() -> Path:
    """Resolve the user site path, honoring overrides via DOTCANVAS_USER_SITE."""
    override = os.environ.get("DOTCANVAS_USER_SITE")
    if override:
        return Path(override).expanduser()
    return _DEF_USER_SITE


def _manifest_path(user_site: Path) -> Path:
    return user_site / _MANIFEST_FILENAME


def _load_manifest(manifest: Path) -> set[str]:
    if not manifest.exists():
        return set()
    try:
        data = json.loads(manifest.read_text())
        if isinstance(data, list):
            return {str(item) for item in data}
    except json.JSONDecodeError:
        logger.warning("Manifest %s is corrupted; resetting", manifest)
    return set()


def _save_manifest(manifest: Path, packages: Iterable[str]) -> None:
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(sorted({str(pkg) for pkg in packages})))


def ensure_user_site() -> Path:
    """Create and register the writable user site directory."""
    user_site = _resolve_user_site()
    user_site.mkdir(parents=True, exist_ok=True)

    # Ensure imports discover packages from the user site first.
    user_site_str = str(user_site)
    if user_site_str not in sys.path:
        sys.path.insert(0, user_site_str)

    # Keep PYTHONPATH in sync for subprocesses that might be spawned later.
    existing_pythonpath = os.environ.get("PYTHONPATH")
    if existing_pythonpath:
        paths = existing_pythonpath.split(os.pathsep)
        if user_site_str not in paths:
            os.environ["PYTHONPATH"] = os.pathsep.join([user_site_str, existing_pythonpath])
    else:
        os.environ["PYTHONPATH"] = user_site_str

    return user_site


def install_package(*packages: str) -> None:
    """Install one or more packages into the writable user site directory."""
    normalized = [pkg.strip() for pkg in packages if pkg and pkg.strip()]
    if not normalized:
        raise ValueError("At least one package name is required")

    # Lazily ensure the directory exists and is importable before installing.
    user_site = ensure_user_site()
    manifest = _manifest_path(user_site)
    installed = _load_manifest(manifest)

    to_install = [pkg for pkg in normalized if pkg not in installed]
    if not to_install:
        # logger.info("Packages %s already installed; skipping", normalized)
        return

    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-cache-dir",
        "--target",
        str(user_site),
    ]
    cmd.extend(to_install)

    logger.info("Installing packages %s into %s", to_install, user_site)
    subprocess.check_call(cmd)
    importlib.invalidate_caches()
    _save_manifest(manifest, installed.union(to_install))


def install_packages(packages: Iterable[str]) -> None:
    """Install a collection of packages into the user site directory."""
    install_package(*list(packages))


# Ensure the user site is ready as soon as this module is imported.
ensure_user_site()

__all__ = ["install_package", "install_packages", "ensure_user_site"]
