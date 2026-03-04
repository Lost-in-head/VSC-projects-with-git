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
    assert suggest_price([]) == 0.0


def test_build_listing_payload_shape():
    payload = build_listing_payload("Test Title", "Test desc", 299.99, "Like New")
    assert payload["price"]["value"] == "299.99"
    assert payload["condition"] == "Like New"
