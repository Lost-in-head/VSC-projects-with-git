"""
Platform-aware data directory resolution.

Provides portable paths for the database and uploads folder so the app
works correctly when installed as a packaged desktop application (where
the source tree may be read-only).

Override the base directory at any time with the CARDS4SALE_DATA_DIR
environment variable — useful for tests and CI.
"""

import os
from pathlib import Path

try:
    import platformdirs
    _HAS_PLATFORMDIRS = True
except ImportError:
    _HAS_PLATFORMDIRS = False

APP_NAME = "Cards4Sale"


def get_data_dir() -> Path:
    """Return the platform-appropriate user data directory.

    Resolution order:
    1. ``CARDS4SALE_DATA_DIR`` env var (tests / CI override)
    2. ``platformdirs.user_data_dir`` when the package is available
    3. Repo-root fallback (original behaviour — keeps existing installs working)
    """
    override = os.environ.get("CARDS4SALE_DATA_DIR")
    if override:
        return Path(override)

    if _HAS_PLATFORMDIRS:
        return Path(platformdirs.user_data_dir(APP_NAME))

    # Fallback: place data next to the repo root (original behaviour)
    return Path(__file__).parent.parent


def get_db_path() -> Path:
    """Return the full path to the SQLite database file."""
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "listings.db"


def get_upload_dir() -> str:
    """Return the uploads directory path as a string, creating it if needed."""
    data_dir = get_data_dir()
    upload_dir = data_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return str(upload_dir)
