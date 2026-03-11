from src.api.mock_openai import describe_image_mock
from src.api.mock_ebay import search_ebay_mock


REQUIRED_IMAGE_KEYS = [
    "brand",
    "model",
    "category",
    "condition",
    "features",
    "estimated_value_range",
]


def test_describe_image_mock_shape():
    result = describe_image_mock("anything.jpg")
    assert isinstance(result, dict)
    assert all(key in result for key in REQUIRED_IMAGE_KEYS)
    assert isinstance(result["features"], list)


def test_search_ebay_mock_returns_limited_results():
    results = search_ebay_mock("MacBook Air", limit=3)
    assert len(results) == 3
    assert all("title" in item and "price" in item and "url" in item for item in results)
    assert all(isinstance(item["price"], float) for item in results)


def test_describe_image_mock_supports_multi_card_shape():
    result = describe_image_mock("multi_cards.jpg")
    assert "cards" in result
    assert isinstance(result["cards"], list)
    assert len(result["cards"]) >= 2
