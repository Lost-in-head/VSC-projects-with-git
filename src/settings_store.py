"""
Settings store for Cards 4 Sale.

Provides a portable credential/settings store that:
  1. Tries the OS keychain via the ``keyring`` library (secure on macOS/Windows/Linux
     with a secret service daemon running).
  2. Falls back to a JSON file in the user data directory when no OS keychain is
     available (e.g., headless servers, CI, fresh Linux installs without a running
     secret-service).

The fallback file lives at ``get_data_dir() / "settings.json"`` and is readable
only by the current user (permissions are set to 0o600 on POSIX systems).

Stored keys
-----------
Credentials (sensitive — keyring preferred):
    OPENAI_API_KEY, EBAY_CLIENT_ID, EBAY_CLIENT_SECRET

Toggles (non-sensitive booleans stored as string "True"/"False"):
    USE_OPENAI_MOCK, USE_EBAY_MOCK, EBAY_SANDBOX

Usage
-----
    from src.settings_store import load_all, save_all, apply_to_env

    # At app startup (before config.py is evaluated):
    apply_to_env()

    # In the /api/settings POST handler:
    save_all({"OPENAI_API_KEY": "sk-...", "USE_OPENAI_MOCK": "False"})
"""

import json
import logging
import os
import stat
from pathlib import Path

from src.paths import get_data_dir

logger = logging.getLogger(__name__)

_SERVICE_NAME = "Cards4Sale"

# All keys managed by this store
CREDENTIAL_KEYS: frozenset[str] = frozenset(
    {"OPENAI_API_KEY", "EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET"}
)
TOGGLE_KEYS: frozenset[str] = frozenset(
    {"USE_OPENAI_MOCK", "USE_EBAY_MOCK", "EBAY_SANDBOX"}
)
ALL_KEYS: frozenset[str] = CREDENTIAL_KEYS | TOGGLE_KEYS


# ── Keyring helpers ───────────────────────────────────────────────────────────

def _keyring_get(key: str) -> str | None:
    try:
        import keyring
        return keyring.get_password(_SERVICE_NAME, key)
    except Exception:
        return None


def _keyring_set(key: str, value: str) -> bool:
    """Return True on success, False if no OS keychain is available."""
    try:
        import keyring
        keyring.set_password(_SERVICE_NAME, key, value)
        return True
    except Exception:
        return False


def _keyring_delete(key: str) -> None:
    try:
        import keyring
        keyring.delete_password(_SERVICE_NAME, key)
    except Exception:
        pass


# ── File fallback helpers ─────────────────────────────────────────────────────

def _fallback_path() -> Path:
    return get_data_dir() / "settings.json"


def _load_fallback() -> dict:
    path = _fallback_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Could not read settings file %s: %s", path, exc)
    return {}


def _save_fallback(data: dict) -> None:
    path = _fallback_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # Restrict file permissions on POSIX (owner read/write only)
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # Windows or permission error — not critical


# ── Public API ────────────────────────────────────────────────────────────────

def get_credential(key: str) -> str | None:
    """Return a stored credential, or None if not set."""
    value = _keyring_get(key)
    if value is not None:
        return value
    return _load_fallback().get(key)


def save_credential(key: str, value: str) -> None:
    """Persist a credential to the OS keychain if available, else to the fallback file."""
    if not _keyring_set(key, value):
        data = _load_fallback()
        data[key] = value
        _save_fallback(data)
        logger.debug("Saved %s to fallback settings file", key)


def delete_credential(key: str) -> None:
    """Remove a stored credential from both keychain and fallback file."""
    _keyring_delete(key)
    data = _load_fallback()
    if key in data:
        del data[key]
        _save_fallback(data)


def load_all() -> dict:
    """Return all currently stored settings as a plain dict."""
    result = {}
    for key in ALL_KEYS:
        val = get_credential(key)
        if val is not None:
            result[key] = val
    return result


def save_all(settings: dict) -> None:
    """
    Save a dict of settings.  Only keys present in ALL_KEYS are persisted;
    unknown keys are silently ignored.
    """
    for key, value in settings.items():
        if key in ALL_KEYS:
            if not value:
                # Treat empty string / None as "delete this credential"
                delete_credential(key)
            else:
                save_credential(key, str(value))


def apply_to_env() -> None:
    """
    Load all stored settings and push them into ``os.environ``.

    Call this **before** importing ``src.config`` so that the loaded values
    take precedence over the ``.env`` file.
    """
    stored = load_all()
    for key, value in stored.items():
        os.environ[key] = value
        logger.debug("Applied stored setting %s to environment", key)
    if stored:
        logger.info("Applied %d stored setting(s) from settings store", len(stored))
