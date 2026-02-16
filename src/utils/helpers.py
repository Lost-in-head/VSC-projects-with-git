"""
Helper utilities
"""


def format_price(price: float) -> str:
    """Format price as USD."""
    return f"${price:.2f}"


def clean_title(title: str, max_length: int = 80) -> str:
    """Clean and trim eBay listing title."""
    title = title.strip()
    if len(title) > max_length:
        title = title[:max_length].rsplit(' ', 1)[0]
    return title
