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

# package_manager.py -> canvas_runtime/ -> src/ -> project root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
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

    logger.info("Installing packages %s into %s", to_install, user_site)
    _run_pip_install(to_install, user_site)
    importlib.invalidate_caches()
    _save_manifest(manifest, installed.union(to_install))


def _run_pip_install(packages: list[str], user_site: Path) -> None:
    """Install packages with `python -m pip`, bootstrapping pip if needed."""
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-cache-dir",
        "--prefer-binary",
        "--target",
        str(user_site),
        *packages,
    ]

    try:
        _invoke_pip(cmd)
        return
    except subprocess.CalledProcessError as exc:
        # uv-managed venvs often omit pip; bootstrap it once and retry.
        if not _ensure_pip_available():
            raise _pip_install_error(packages, exc) from exc
        logger.info("Retrying package install after bootstrapping pip")
        try:
            _invoke_pip(cmd)
        except subprocess.CalledProcessError as retry_exc:
            raise _pip_install_error(packages, retry_exc) from retry_exc


def _invoke_pip(cmd: list[str]) -> None:
    """Run pip and surface its combined output on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        if result.stdout.strip():
            logger.info(result.stdout.rstrip())
        return
    combined = "\n".join(
        part for part in (result.stdout, result.stderr) if part and part.strip()
    ).strip()
    if combined:
        logger.error(combined)
    raise subprocess.CalledProcessError(
        result.returncode,
        cmd,
        output=result.stdout,
        stderr=result.stderr,
    )


def _pip_install_error(
    packages: list[str], exc: subprocess.CalledProcessError
) -> RuntimeError:
    """Build a clearer error when pip cannot install into user_site."""
    py_tag = f"{sys.version_info.major}.{sys.version_info.minor}"
    detail = (exc.stderr or exc.output or "").strip()
    if len(detail) > 2000:
        detail = detail[-2000:]
    hint = (
        f"Failed to install {packages!r} into user_site for Python {py_tag}. "
        "Prefer packages that publish binary wheels for this Python version; "
        "source builds need a compiler (Docker images include build-essential)."
    )
    if detail:
        return RuntimeError(f"{hint}\n\nPip output (tail):\n{detail}")
    return RuntimeError(hint)


def _ensure_pip_available() -> bool:
    """Return True when `python -m pip` works, installing pip if necessary."""
    probe = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        check=False,
    )
    if probe.returncode == 0:
        return True

    logger.warning("pip is unavailable in %s; attempting bootstrap", sys.executable)
    bootstrap = subprocess.run(
        [sys.executable, "-m", "ensurepip", "--upgrade"],
        capture_output=True,
        check=False,
    )
    if bootstrap.returncode != 0:
        logger.error(
            "Failed to bootstrap pip via ensurepip: %s",
            bootstrap.stderr.decode(errors="ignore").strip() or bootstrap.stdout.decode(errors="ignore").strip(),
        )
        return False

    probe = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        check=False,
    )
    return probe.returncode == 0


def install_packages(packages: Iterable[str]) -> None:
    """Install a collection of packages into the user site directory."""
    install_package(*list(packages))


# Ensure the user site is ready as soon as this module is imported.
ensure_user_site()

__all__ = ["install_package", "install_packages", "ensure_user_site"]
