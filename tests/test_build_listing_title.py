"""
Direct unit tests for src/app._build_listing_title.

The function is not exported but it is importable; we call it directly to
exercise every branch without needing the full pipeline.
"""
from src.app import _build_listing_title


class TestBuildListingTitle:
    def test_card_category_prepends_player_name_when_absent_from_model(self):
        """Player name must be prepended when it is not present in the model string."""
        analysis = {
            "brand": "Topps",
            "model": "Rookie Card",
            "category": "Sports Trading Cards",
            "player_name": "Mike Trout",
        }
        title = _build_listing_title(analysis)
        assert title.startswith("Mike Trout")
        assert "Topps" in title
        assert "Rookie Card" in title

    def test_card_category_does_not_duplicate_player_name_already_in_model(self):
        """Player name must not be prepended when it is already in the model string."""
        analysis = {
            "brand": "Topps",
            "model": "Mike Trout Rookie Card",
            "category": "Sports Trading Cards",
            "player_name": "Mike Trout",
        }
        title = _build_listing_title(analysis)
        assert title.count("Mike Trout") == 1

    def test_card_category_without_player_name_returns_brand_model(self):
        """When player_name is absent the title should be 'brand model'."""
        analysis = {
            "brand": "Panini",
            "model": "Base Card",
            "category": "Sports Trading Cards",
        }
        title = _build_listing_title(analysis)
        assert title == "Panini Base Card"

    def test_non_card_category_uses_brand_model(self):
        """Non-card categories should always produce a 'brand model' title."""
        analysis = {
            "brand": "Sony",
            "model": "WH-1000XM4",
            "category": "Electronics",
            "player_name": "Should Not Appear",
        }
        title = _build_listing_title(analysis)
        assert title == "Sony WH-1000XM4"
        assert "Should Not Appear" not in title

    def test_missing_brand_defaults_to_item(self):
        """When brand is absent the default 'Item' placeholder should be used."""
        analysis = {"model": "Unknown Object", "category": "Other"}
        title = _build_listing_title(analysis)
        assert "Item" in title
        assert "Unknown Object" in title

    def test_empty_model_does_not_produce_trailing_whitespace(self):
        """A title with an empty model should not have trailing spaces."""
        analysis = {"brand": "Nike", "model": "", "category": "Shoes"}
        title = _build_listing_title(analysis)
        assert title == "Nike"
