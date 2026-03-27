"""
Tests for the D7 Settings routes (/settings, /api/settings) and settings_store.
"""
import json
import os
import pytest

from src.app import create_app
import src.database as db
import src.settings_store as settings_store


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "test_listings.db")
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """Redirect settings store to a temp directory so tests don't pollute the
    user's real settings file, and patch out the OS keyring to avoid errors in
    headless CI environments."""
    monkeypatch.setenv("CARDS4SALE_DATA_DIR", str(tmp_path))

    # Stub keyring to always fail so we exercise the file fallback
    monkeypatch.setattr(settings_store, "_keyring_get", lambda key: None)
    monkeypatch.setattr(settings_store, "_keyring_set", lambda key, value: False)
    monkeypatch.setattr(settings_store, "_keyring_delete", lambda key: None)

    yield


# ── settings_store unit tests ─────────────────────────────────────────────────

class TestSettingsStore:
    def test_round_trip_credential(self, tmp_path):
        settings_store.save_credential("OPENAI_API_KEY", "sk-test123")
        assert settings_store.get_credential("OPENAI_API_KEY") == "sk-test123"

    def test_missing_credential_returns_none(self):
        assert settings_store.get_credential("OPENAI_API_KEY") is None

    def test_delete_credential(self, tmp_path):
        settings_store.save_credential("EBAY_CLIENT_ID", "app-id-xyz")
        settings_store.delete_credential("EBAY_CLIENT_ID")
        assert settings_store.get_credential("EBAY_CLIENT_ID") is None

    def test_save_all_filters_unknown_keys(self, tmp_path):
        settings_store.save_all({"UNKNOWN_KEY": "should-be-ignored", "USE_EBAY_MOCK": "True"})
        assert settings_store.get_credential("UNKNOWN_KEY") is None
        assert settings_store.get_credential("USE_EBAY_MOCK") == "True"

    def test_load_all_returns_stored_keys(self, tmp_path):
        settings_store.save_credential("OPENAI_API_KEY", "sk-abc")
        settings_store.save_credential("USE_OPENAI_MOCK", "True")
        result = settings_store.load_all()
        assert result["OPENAI_API_KEY"] == "sk-abc"
        assert result["USE_OPENAI_MOCK"] == "True"

    def test_empty_string_deletes_credential(self, tmp_path):
        settings_store.save_credential("OPENAI_API_KEY", "sk-delete-me")
        settings_store.save_all({"OPENAI_API_KEY": ""})
        assert settings_store.get_credential("OPENAI_API_KEY") is None

    def test_apply_to_env_sets_environ(self, monkeypatch, tmp_path):
        settings_store.save_credential("OPENAI_API_KEY", "sk-env-test")
        settings_store.apply_to_env()
        assert os.environ.get("OPENAI_API_KEY") == "sk-env-test"

    def test_settings_file_has_restricted_permissions(self, tmp_path):
        import stat as stat_mod
        import sys
        settings_store.save_credential("OPENAI_API_KEY", "sk-perm-test")
        path = settings_store._fallback_path()
        assert path.exists()
        if sys.platform != "win32":
            mode = path.stat().st_mode
            assert not (mode & stat_mod.S_IRGRP), "Group should not have read permission"
            assert not (mode & stat_mod.S_IROTH), "Others should not have read permission"


# ── Settings API route tests ──────────────────────────────────────────────────

class TestSettingsRoutes:
    def test_settings_page_renders(self, client):
        res = client.get("/settings")
        assert res.status_code == 200
        assert b"Settings" in res.data

    def test_get_settings_returns_json(self, client):
        res = client.get("/api/settings")
        assert res.status_code == 200
        data = res.get_json()
        assert "openai_api_key_set" in data
        assert "use_openai_mock" in data
        assert "use_ebay_mock" in data
        assert "ebay_sandbox" in data

    def test_get_settings_key_not_set_by_default(self, client):
        res = client.get("/api/settings")
        data = res.get_json()
        assert data["openai_api_key_set"] is False
        assert data["ebay_client_id_set"] is False

    def test_post_settings_saves_toggles(self, client):
        res = client.post(
            "/api/settings",
            json={"USE_OPENAI_MOCK": True, "USE_EBAY_MOCK": False, "EBAY_SANDBOX": True},
        )
        assert res.status_code == 200
        assert res.get_json()["success"] is True
        # Verify persisted
        assert settings_store.get_credential("USE_OPENAI_MOCK") == "True"
        assert settings_store.get_credential("USE_EBAY_MOCK") == "False"
        assert settings_store.get_credential("EBAY_SANDBOX") == "True"

    def test_post_settings_saves_api_key(self, client):
        res = client.post("/api/settings", json={"OPENAI_API_KEY": "sk-stored-key"})
        assert res.status_code == 200
        assert settings_store.get_credential("OPENAI_API_KEY") == "sk-stored-key"

    def test_get_settings_after_save_shows_key_set(self, client):
        client.post("/api/settings", json={"OPENAI_API_KEY": "sk-visible"})
        res = client.get("/api/settings")
        data = res.get_json()
        assert data["openai_api_key_set"] is True
        # Preview should be masked — not the full key
        assert data["openai_api_key_preview"] != "sk-visible"
        assert "sk-" in data["openai_api_key_preview"]

    def test_post_settings_empty_body_returns_success(self, client):
        res = client.post("/api/settings", json={})
        assert res.status_code == 200
        assert res.get_json()["success"] is True

    def test_test_openai_returns_mock_status_in_mock_mode(self, client, monkeypatch):
        monkeypatch.setenv("USE_OPENAI_MOCK", "True")
        # Reload config so mock mode is active
        import importlib, src.config as cfg
        monkeypatch.setattr(cfg, "USE_OPENAI_MOCK", True)
        res = client.post("/api/settings/test-openai")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["mode"] == "mock"

    def test_test_ebay_returns_mock_status_in_mock_mode(self, client, monkeypatch):
        import src.config as cfg
        monkeypatch.setattr(cfg, "USE_EBAY_MOCK", True)
        res = client.post("/api/settings/test-ebay")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["mode"] == "mock"

    def test_test_openai_no_key_returns_mock_mode(self, client, monkeypatch):
        import src.config as cfg
        monkeypatch.setattr(cfg, "USE_OPENAI_MOCK", False)
        monkeypatch.setattr(cfg, "OPENAI_API_KEY", None)
        res = client.post("/api/settings/test-openai")
        data = res.get_json()
        assert data["success"] is True
        assert data["mode"] == "mock"

    def test_test_ebay_no_credentials_returns_mock_mode(self, client, monkeypatch):
        import src.config as cfg
        monkeypatch.setattr(cfg, "USE_EBAY_MOCK", False)
        monkeypatch.setattr(cfg, "EBAY_CLIENT_ID", None)
        monkeypatch.setattr(cfg, "EBAY_CLIENT_SECRET", None)
        res = client.post("/api/settings/test-ebay")
        data = res.get_json()
        assert data["success"] is True
        assert data["mode"] == "mock"
