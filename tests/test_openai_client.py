"""
Tests for src/api/openai_client.py — real-API-mode paths.

The conftest autouse fixture enables mock mode for every test, so these tests
explicitly override USE_OPENAI_MOCK and OPENAI_API_KEY at the module level to
exercise the branches that only run when a real API key is configured.
"""
import json
import pytest
import requests

import src.api.openai_client as openai_client


@pytest.fixture
def real_mode(monkeypatch):
    """Switch the openai_client module to real-API mode with a fake key."""
    monkeypatch.setattr(openai_client, "USE_OPENAI_MOCK", False)
    monkeypatch.setattr(openai_client, "OPENAI_API_KEY", "fake-test-key")


def _make_fake_response(content):
    """Return a minimal requests.Response-like object with the given content string."""
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": content}}]}

    return FakeResponse()


# ---------------------------------------------------------------------------
# Fallback paths (real mode, but something goes wrong)
# ---------------------------------------------------------------------------

def test_describe_image_file_not_found_falls_back_to_mock(real_mode):
    """When the image file does not exist in real mode, fall back to mock data."""
    result = openai_client.describe_image("/nonexistent/path/image.jpg")
    assert isinstance(result, dict)
    assert "brand" in result


def test_describe_image_api_exception_falls_back_to_mock(real_mode, monkeypatch, tmp_path):
    """When the HTTP call raises an exception in real mode, fall back to mock data."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"FAKE_JPEG_DATA")

    def raise_error(*args, **kwargs):
        raise ConnectionError("simulated network failure")

    monkeypatch.setattr(requests, "post", raise_error)

    result = openai_client.describe_image(str(img_path))
    assert isinstance(result, dict)
    assert "brand" in result


# ---------------------------------------------------------------------------
# Successful real API call
# ---------------------------------------------------------------------------

def test_describe_image_successful_real_api_call(real_mode, monkeypatch, tmp_path):
    """A successful real API call should return the parsed JSON analysis."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"FAKE_JPEG_DATA")

    expected = {
        "brand": "Topps",
        "model": "Rookie Card",
        "category": "Sports Trading Cards",
        "condition": "Near Mint",
        "features": ["Rookie"],
        "estimated_value_range": "$10-20",
        "grading_notes": [],
    }

    monkeypatch.setattr(requests, "post", lambda *a, **kw: _make_fake_response(json.dumps(expected)))

    result = openai_client.describe_image(str(img_path))
    assert result["brand"] == "Topps"
    assert result["model"] == "Rookie Card"
    assert result["condition"] == "Near Mint"


# ---------------------------------------------------------------------------
# JSON parsing edge cases
# ---------------------------------------------------------------------------

def test_describe_image_extracts_json_from_response_with_extra_text(real_mode, monkeypatch, tmp_path):
    """JSON should be extracted even when the response has extra surrounding text."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"FAKE_JPEG_DATA")

    inner = {
        "brand": "Sony",
        "model": "WH-1000XM4",
        "category": "Electronics",
        "condition": "Good",
        "features": [],
        "estimated_value_range": "$200-300",
    }
    wrapped = f"Here is the analysis:\n{json.dumps(inner)}\nEnd of analysis."

    monkeypatch.setattr(requests, "post", lambda *a, **kw: _make_fake_response(wrapped))

    result = openai_client.describe_image(str(img_path))
    assert result["brand"] == "Sony"
    assert result["model"] == "WH-1000XM4"


def test_describe_image_non_json_response_returns_fallback_dict(real_mode, monkeypatch, tmp_path):
    """When the response contains no valid JSON, return the hard-coded fallback dict."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"FAKE_JPEG_DATA")

    monkeypatch.setattr(
        requests, "post", lambda *a, **kw: _make_fake_response("This is not JSON at all.")
    )

    result = openai_client.describe_image(str(img_path))
    assert isinstance(result, dict)
    assert result.get("brand") == "Unknown"
    assert result.get("condition") == "Good"
    assert result.get("category") == "Other"


# ---------------------------------------------------------------------------
# Media-type detection
# ---------------------------------------------------------------------------

def test_describe_image_uses_png_media_type(real_mode, monkeypatch, tmp_path):
    """PNG files should be sent with image/png content-type in the data URI."""
    img_path = tmp_path / "test.png"
    img_path.write_bytes(b"FAKE_PNG_DATA")

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"brand":"X","model":"Y","category":"Z","condition":"Good","features":[],"estimated_value_range":"$1-2"}'
                        }
                    }
                ]
            }

    def fake_post(url, headers, json=None, timeout=None):
        captured["payload"] = json
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    openai_client.describe_image(str(img_path))

    content = captured["payload"]["messages"][0]["content"]
    image_url = content[1]["image_url"]["url"]
    assert image_url.startswith("data:image/png;base64,")


def test_describe_image_uses_gif_media_type(real_mode, monkeypatch, tmp_path):
    """GIF files should be sent with image/gif content-type in the data URI."""
    img_path = tmp_path / "test.gif"
    img_path.write_bytes(b"FAKE_GIF_DATA")

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"brand":"X","model":"Y","category":"Z","condition":"Good","features":[],"estimated_value_range":"$1-2"}'
                        }
                    }
                ]
            }

    def fake_post(url, headers, json=None, timeout=None):
        captured["payload"] = json
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    openai_client.describe_image(str(img_path))

    content = captured["payload"]["messages"][0]["content"]
    image_url = content[1]["image_url"]["url"]
    assert image_url.startswith("data:image/gif;base64,")


def test_describe_image_defaults_to_jpeg_for_other_extensions(real_mode, monkeypatch, tmp_path):
    """Non-PNG/GIF extensions should be sent with image/jpeg content-type."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"FAKE_JPEG_DATA")

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"brand":"X","model":"Y","category":"Z","condition":"Good","features":[],"estimated_value_range":"$1-2"}'
                        }
                    }
                ]
            }

    def fake_post(url, headers, json=None, timeout=None):
        captured["payload"] = json
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    openai_client.describe_image(str(img_path))

    content = captured["payload"]["messages"][0]["content"]
    image_url = content[1]["image_url"]["url"]
    assert image_url.startswith("data:image/jpeg;base64,")
