"""Canvas runtime framework: base classes, views, and canvas manager."""

from .package_manager import ensure_user_site, install_package, install_packages

# Ensure the writable user site is importable as soon as the runtime is loaded.
ensure_user_site()

__all__ = [
    "ensure_user_site",
    "install_package",
    "install_packages",
]
