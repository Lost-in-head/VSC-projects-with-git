from src.utils.helpers import format_price, clean_title


def test_format_price():
    assert format_price(123.456) == "$123.46"
    assert format_price(50) == "$50.00"


def test_format_price_zero():
    assert format_price(0) == "$0.00"


def test_format_price_negative():
    assert format_price(-5.0) == "$-5.00"


def test_clean_title_trims_when_over_max_length():
    long_title = "This is a very long listing title that should be trimmed at a word boundary to stay valid for eBay"
    cleaned = clean_title(long_title, max_length=80)

    assert len(cleaned) <= 80
    assert cleaned.startswith("This is a very long listing title")


def test_clean_title_keeps_short_title():
    assert clean_title("Short Title") == "Short Title"


def test_clean_title_exact_max_length_not_trimmed():
    title = "A" * 80
    assert clean_title(title, max_length=80) == title


def test_clean_title_one_over_max_trimmed():
    title = "A" * 81
    result = clean_title(title, max_length=80)
    assert len(result) <= 80


def test_clean_title_no_space_at_boundary():
    """A word with no internal spaces is trimmed to exactly max_length."""
    title = "A" * 90
    result = clean_title(title, max_length=80)
    assert len(result) <= 80
