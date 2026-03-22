from src.api.openai_client import describe_image
from src.api.ebay_client import search_ebay, suggest_price, build_listing_payload


def test_describe_image_mock_fallback():
    result = describe_image("nonexistent.jpg")
    assert isinstance(result, dict)
    assert "brand" in result


def test_search_ebay_mock_results_shape():
    listings = search_ebay("Sony headphones", limit=4)
    assert len(listings) <= 4
    assert all(isinstance(item["price"], float) for item in listings)


def test_suggest_price_median_and_empty_case():
    listings = [{"price": 100}, {"price": 200}, {"price": 150}]
    assert suggest_price(listings) == 150.0
    assert suggest_price([]) is None


def test_suggest_price_skips_listings_without_price_key():
    """suggest_price must not raise when some listings lack a 'price' key."""
    listings = [{"title": "No price here"}, {"price": 50.0}, {"price": 100.0}]
    result = suggest_price(listings)
    assert result == 75.0


def test_suggest_price_all_listings_missing_price_returns_none():
    listings = [{"title": "No price"}, {"title": "Also no price"}]
    assert suggest_price(listings) is None


def test_build_listing_payload_shape():
    payload = build_listing_payload("Test Title", "Test desc", 299.99, "Like New")
    assert payload["price"]["value"] == "299.99"
    assert payload["condition"] == "Like New"


def test_build_listing_payload_generates_unique_skus():
    payload1 = build_listing_payload("Item A", "Desc A", 10.00)
    payload2 = build_listing_payload("Item B", "Desc B", 20.00)
    assert payload1["sku"] != payload2["sku"]
    assert payload1["sku"].startswith("LISTING-")
    assert payload2["sku"].startswith("LISTING-")


def test_build_listing_payload_long_title_trimmed_at_word_boundary():
    """Titles longer than 80 chars should be trimmed at a word boundary."""
    long_title = "This is an extremely long eBay listing title that exceeds the eighty character limit for eBay listings"
    payload = build_listing_payload(long_title, "desc", 10.0)
    assert len(payload["product"]["title"]) <= 80
