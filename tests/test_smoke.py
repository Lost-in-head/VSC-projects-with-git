from src.api.openai_client import describe_image
from src.api.ebay_client import search_ebay


def test_describe_image_smoke_returns_expected_shape():
    result = describe_image("nonexistent.jpg")

    assert isinstance(result, dict)
    assert "brand" in result
    assert "model" in result
    assert "category" in result
    assert "condition" in result
    assert "features" in result


def test_search_ebay_smoke_returns_list_of_items():
    result = search_ebay("vintage radio", limit=3)

    assert isinstance(result, list)
    if result:
        first = result[0]
        assert isinstance(first, dict)
        assert "title" in first
        assert "price" in first
        assert "url" in first
