"""
Tests for src/api/ebay_client.py — real-API-mode paths and get_ebay_token.

The conftest autouse fixture enables mock mode for every test (USE_EBAY_MOCK=True)
and leaves credentials unset.  These tests explicitly override module-level
attributes to exercise branches that only run with real credentials or real mode.
"""
import pytest
import requests

import src.api.ebay_client as ebay_client


@pytest.fixture
def real_ebay_mode(monkeypatch):
    """Switch ebay_client to real-API mode with fake credentials."""
    monkeypatch.setattr(ebay_client, "USE_EBAY_MOCK", False)
    monkeypatch.setattr(ebay_client, "EBAY_CLIENT_ID", "fake-client-id")
    monkeypatch.setattr(ebay_client, "EBAY_CLIENT_SECRET", "fake-client-secret")


# ---------------------------------------------------------------------------
# get_ebay_token
# ---------------------------------------------------------------------------

def test_get_ebay_token_raises_when_credentials_missing():
    """get_ebay_token should raise ValueError when credentials are not set."""
    # conftest leaves EBAY_CLIENT_ID / EBAY_CLIENT_SECRET as None
    with pytest.raises(ValueError, match="eBay credentials not set"):
        ebay_client.get_ebay_token()


def test_get_ebay_token_success(real_ebay_mode, monkeypatch):
    """get_ebay_token should return the access_token from a successful HTTP response."""

    class FakeTokenResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"access_token": "real-token-abc123"}

    monkeypatch.setattr(requests, "post", lambda *a, **kw: FakeTokenResponse())

    token = ebay_client.get_ebay_token()
    assert token == "real-token-abc123"


# ---------------------------------------------------------------------------
# search_ebay real mode
# ---------------------------------------------------------------------------

def test_search_ebay_real_mode_success(real_ebay_mode, monkeypatch):
    """search_ebay in real mode should parse eBay Finding API JSON correctly."""
    mock_api_data = {
        "findItemsByKeywordsResponse": [
            {
                "searchResult": [
                    {
                        "item": [
                            {
                                "title": ["Sony WH-1000XM4"],
                                "sellingStatus": [{"currentPrice": [{"__value__": "280.00"}]}],
                                "viewItemURL": ["https://www.ebay.com/itm/12345"],
                            }
                        ]
                    }
                ]
            }
        ]
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return mock_api_data

    monkeypatch.setattr(requests, "get", lambda *a, **kw: FakeResponse())

    results = ebay_client.search_ebay("Sony WH-1000XM4", limit=1)
    assert len(results) == 1
    assert results[0]["title"] == "Sony WH-1000XM4"
    assert results[0]["price"] == 280.0
    assert results[0]["url"] == "https://www.ebay.com/itm/12345"


def test_search_ebay_real_mode_empty_results(real_ebay_mode, monkeypatch):
    """search_ebay should return an empty list when the API returns no items."""
    empty_response = {"findItemsByKeywordsResponse": [{"searchResult": [{}]}]}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return empty_response

    monkeypatch.setattr(requests, "get", lambda *a, **kw: FakeResponse())

    results = ebay_client.search_ebay("xyzzy nonexistent item", limit=5)
    assert results == []


def test_search_ebay_real_mode_api_exception_falls_back_to_mock(real_ebay_mode, monkeypatch):
    """search_ebay should fall back to mock data when the HTTP call fails."""

    def raise_error(*args, **kwargs):
        raise ConnectionError("simulated network failure")

    monkeypatch.setattr(requests, "get", raise_error)

    results = ebay_client.search_ebay("laptop", limit=3)
    assert isinstance(results, list)
    assert all("title" in r and "price" in r and "url" in r for r in results)


# ---------------------------------------------------------------------------
# publish_listing
# ---------------------------------------------------------------------------

def test_publish_listing_mock_mode_returns_mock_prefixed_id():
    """publish_listing in mock mode should return an external_listing_id prefixed with MOCK-."""
    payload = {"sku": "TEST-SKU-123", "product": {"title": "Test Item"}}
    result = ebay_client.publish_listing(payload)
    assert result["status"] == "published"
    assert result["external_listing_id"] == "MOCK-TEST-SKU-123"
    assert result["mode"] == "mock"


def test_publish_listing_real_mode_success(real_ebay_mode, monkeypatch):
    """publish_listing in real mode should call the eBay Inventory API and return real mode result."""
    monkeypatch.setattr(ebay_client, "EBAY_API_ENDPOINT", "https://api.sandbox.ebay.com")

    class FakeTokenResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"access_token": "fake-bearer-token"}

    class FakePutResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {}

    monkeypatch.setattr(requests, "post", lambda *a, **kw: FakeTokenResponse())
    monkeypatch.setattr(requests, "put", lambda *a, **kw: FakePutResponse())

    payload = {"sku": "REAL-SKU-999", "product": {"title": "Real Item"}}
    result = ebay_client.publish_listing(payload)
    assert result["status"] == "published"
    assert result["external_listing_id"] == "REAL-SKU-999"
    assert result["mode"] == "real"
