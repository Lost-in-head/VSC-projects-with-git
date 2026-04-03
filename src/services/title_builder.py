"""
TitleBuilder — constructs SEO-optimised eBay listing titles.

Extracted from app._build_listing_title() for testability and reuse.
"""
import logging

logger = logging.getLogger(__name__)


class TitleBuilder:
    """Builds SEO-optimised eBay listing titles."""

    def __init__(self, max_length: int = 80):
        self.max_length = max_length

    def build(self, analysis: dict) -> str:
        """Build a title based on item type."""
        if self._is_trading_card(analysis):
            title = self._build_card_title(analysis)
        else:
            title = self._build_generic_title(analysis)
        return title[: self.max_length].strip()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_trading_card(analysis: dict) -> bool:
        return 'card' in (analysis.get('category') or '').lower()

    @staticmethod
    def _build_card_title(analysis: dict) -> str:
        brand = analysis.get('brand', 'Item')
        model = analysis.get('model', '')
        player_name = analysis.get('player_name', '')
        # Prepend player name only when it is not already present in the model string
        if player_name and player_name.lower() not in model.lower():
            return f"{player_name} {brand} {model}".strip()
        return f"{brand} {model}".strip()

    @staticmethod
    def _build_generic_title(analysis: dict) -> str:
        brand = analysis.get('brand', 'Item')
        model = analysis.get('model', '')
        return f"{brand} {model}".strip()
