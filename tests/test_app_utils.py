"""
Unit tests for app utility functions:
allowed_file, format_description, build_search_query, normalize_analysis_cards
"""
import pytest
from src.app import allowed_file, format_description, build_search_query, normalize_analysis_cards


# ---------------------------------------------------------------------------
# allowed_file
# ---------------------------------------------------------------------------

class TestAllowedFile:
    def test_jpg(self):
        assert allowed_file("photo.jpg") is True

    def test_jpeg(self):
        assert allowed_file("photo.jpeg") is True

    def test_png(self):
        assert allowed_file("photo.png") is True

    def test_gif(self):
        assert allowed_file("animation.gif") is True

    def test_uppercase_extension(self):
        assert allowed_file("photo.JPG") is True

    def test_exe_rejected(self):
        assert allowed_file("evil.exe") is False

    def test_php_rejected(self):
        assert allowed_file("script.php") is False

    def test_txt_rejected(self):
        assert allowed_file("readme.txt") is False

    def test_no_extension_rejected(self):
        assert allowed_file("no_extension") is False


# ---------------------------------------------------------------------------
# format_description
# ---------------------------------------------------------------------------

class TestFormatDescription:
    def test_normal_input(self):
        analysis = {
            "category": "Electronics",
            "condition": "Used",
            "brand": "Sony",
            "model": "WH-1000XM4",
            "features": ["Noise Canceling", "Bluetooth"],
            "grading_notes": ["Minor scratch"],
        }
        result = format_description(analysis)
        assert "Electronics" in result
        assert "Used" in result
        assert "Sony" in result
        assert "WH-1000XM4" in result
        assert "Noise Canceling" in result
        assert "Minor scratch" in result

    def test_empty_features_list(self):
        analysis = {
            "category": "Cards",
            "condition": "Near Mint",
            "brand": "Topps",
            "model": "Rookie",
            "features": [],
        }
        result = format_description(analysis)
        assert "Topps" in result
        assert "Features" not in result

    def test_none_values_in_analysis(self):
        analysis = {
            "category": None,
            "condition": None,
            "brand": None,
            "model": None,
        }
        # Should not raise; simply omit None-valued fields
        result = format_description(analysis)
        assert isinstance(result, str)

    def test_grading_notes_as_string(self):
        analysis = {"grading_notes": "Some note as plain string"}
        result = format_description(analysis)
        assert "Some note as plain string" in result


# ---------------------------------------------------------------------------
# build_search_query
# ---------------------------------------------------------------------------

class TestBuildSearchQuery:
    def test_card_category_includes_player_and_set(self):
        analysis = {
            "brand": "Topps",
            "model": "Rookie",
            "category": "Sports Trading Cards",
            "player_name": "Shohei Ohtani",
            "set_name": "Topps Update",
            "year": "2018",
        }
        query = build_search_query(analysis)
        assert "Shohei Ohtani" in query
        assert "Topps Update" in query
        assert "2018" in query

    def test_non_card_path_uses_brand_and_model(self):
        analysis = {
            "brand": "Sony",
            "model": "WH-1000XM4",
            "category": "Electronics",
        }
        query = build_search_query(analysis)
        assert "Sony" in query
        assert "WH-1000XM4" in query
        assert "player_name" not in query

    def test_empty_analysis_returns_fallback(self):
        query = build_search_query({})
        assert query == "collectible trading card"

    def test_partial_card_fields_ignored_for_non_card(self):
        analysis = {
            "brand": "Nike",
            "model": "Air Max",
            "category": "Shoes",
            "player_name": "Should Not Appear",
        }
        query = build_search_query(analysis)
        assert "Should Not Appear" not in query


# ---------------------------------------------------------------------------
# normalize_analysis_cards
# ---------------------------------------------------------------------------

class TestNormalizeAnalysisCards:
    def test_single_item_dict(self):
        analysis = {"brand": "Sony", "model": "WH-1000XM4"}
        result = normalize_analysis_cards(analysis)
        assert result == [analysis]

    def test_multi_card_dict(self):
        cards = [
            {"brand": "Topps", "model": "Card A"},
            {"brand": "Panini", "model": "Card B"},
        ]
        result = normalize_analysis_cards({"cards": cards})
        assert result == cards

    def test_empty_cards_list_falls_back_to_parent(self):
        parent = {"cards": [], "brand": "Fallback"}
        result = normalize_analysis_cards(parent)
        assert result == [parent]

    def test_non_dict_items_in_cards_list_filtered(self):
        cards = [{"brand": "Topps"}, "not_a_dict", None, 42]
        result = normalize_analysis_cards({"cards": cards})
        assert result == [{"brand": "Topps"}]

    def test_empty_dict_returns_list_with_empty_dict(self):
        result = normalize_analysis_cards({})
        assert result == [{}]
