from src.utils.helpers import format_price, clean_title


def test_format_price():
    assert format_price(123.456) == "$123.46"
    assert format_price(50) == "$50.00"


def test_clean_title_trims_when_over_max_length():
    long_title = "This is a very long listing title that should be trimmed at a word boundary to stay valid for eBay"
    cleaned = clean_title(long_title, max_length=80)

    assert len(cleaned) <= 80
    assert cleaned.startswith("This is a very long listing title")


def test_clean_title_keeps_short_title():
    assert clean_title("Short Title") == "Short Title"
