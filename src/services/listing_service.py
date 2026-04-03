"""
ListingService — orchestrates the image-to-listing pipeline.

Extracted from app.py so that route handlers stay thin and business logic
is independently testable.
"""
import logging
import tempfile
import os

from src.services.title_builder import TitleBuilder
from src.services.description_builder import DescriptionBuilder
from src.exceptions import ListingGenerationError

logger = logging.getLogger(__name__)

_title_builder = TitleBuilder()
_description_builder = DescriptionBuilder()


class ListingService:
    """
    Orchestrates the full image → eBay listing pipeline.

    Dependencies are injected so each can be swapped in tests.
    """

    def __init__(
        self,
        describe_image_fn,
        search_ebay_fn,
        suggest_price_fn,
        build_listing_payload_fn,
        save_listing_fn,
        high_value_threshold: float = 20.0,
    ):
        self._describe_image = describe_image_fn
        self._search_ebay = search_ebay_fn
        self._suggest_price = suggest_price_fn
        self._build_listing_payload = build_listing_payload_fn
        self._save_listing = save_listing_fn
        self.high_value_threshold = high_value_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_image(self, image_path: str, filename: str = 'unknown.jpg') -> dict:
        """
        Process a single image through the complete pipeline.

        Returns a normalised dict:
        {
            'success': bool,
            'listings': [ListingResult, ...],   # always a list
            'count': int,
            'high_value_threshold': float,
            'message': str,
            'error': str | None,                # present only on failure
        }
        """
        try:
            logger.info("Analyzing uploaded image: %s", filename)
            image_analysis = self._describe_image(image_path)
            analyses = self._normalize_analyses(image_analysis)

            if not analyses:
                return {
                    'success': False,
                    'listings': [],
                    'count': 0,
                    'high_value_threshold': self.high_value_threshold,
                    'error': 'No items detected in image',
                    'message': '❌ Could not identify any items in the photo',
                }

            logger.info("Searching eBay for %d item(s)…", len(analyses))
            listings = [
                self._generate_one(analysis, filename) for analysis in analyses
            ]
            count = len(listings)
            msg = (
                f"✅ Generated {count} listing draft{'s' if count != 1 else ''} "
                "from one photo."
            )
            return {
                'success': True,
                'listings': listings,
                'count': count,
                'high_value_threshold': self.high_value_threshold,
                'message': msg,
            }

        except Exception as exc:
            logger.exception("ListingService.process_image failed for %s", filename)
            return {
                'success': False,
                'listings': [],
                'count': 0,
                'high_value_threshold': self.high_value_threshold,
                'error': str(exc),
                'message': '❌ Failed to generate listing',
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_one(self, analysis: dict, filename: str) -> dict:
        """Generate and persist one listing for one analysed item."""
        search_query = self._build_search_query(analysis)
        comparable = self._search_ebay(search_query, limit=8)
        suggested_price = self._suggest_price(comparable)

        if suggested_price is None:
            suggested_price = 5.00
            price_warning = True
        else:
            price_warning = False

        title = _title_builder.build(analysis)
        description = _description_builder.build(analysis)
        payload = self._build_listing_payload(
            title=title,
            description=description,
            price=suggested_price,
            condition=analysis.get('condition', 'Unknown'),
        )

        listing_id = self._save_listing(
            title=title,
            filename=filename,
            analysis=analysis,
            comparable_listings=comparable,
            suggested_price=suggested_price,
            payload=payload,
        )

        if listing_id is None:
            raise ListingGenerationError(
                stage='save_listing',
                reason='Database returned None for listing_id',
            )

        return {
            'listing_id': listing_id,
            'analysis': analysis,
            'comparable_listings': comparable,
            'suggested_price': suggested_price,
            'price_warning': price_warning,
            'is_high_value': suggested_price >= self.high_value_threshold,
            'payload': payload,
        }

    @staticmethod
    def _normalize_analyses(image_analysis: dict) -> list:
        """Normalise analysis output to a flat list of item dicts.

        If the analysis has a 'cards' list, each dict element is used directly.
        Non-dict elements in the list are filtered out. An empty cards list (or
        one with no valid dicts) falls back to wrapping the parent dict in a list.
        """
        if not isinstance(image_analysis, dict):
            return []
        if isinstance(image_analysis.get('cards'), list):
            cards = [c for c in image_analysis['cards'] if isinstance(c, dict)]
            # Fall back to parent dict when no valid card dicts were found
            return cards if cards else [image_analysis]
        return [image_analysis]

    @staticmethod
    def _build_search_query(analysis: dict) -> str:
        """Build an eBay search query from an analysis dict."""
        base = [analysis.get('brand', ''), analysis.get('model', '')]
        category = (analysis.get('category') or '').lower()
        if 'card' in category:
            for key in ('player_name', 'set_name', 'year', 'card_number', 'grade'):
                value = analysis.get(key)
                if value:
                    base.append(str(value))
        query = ' '.join(p for p in base if p).strip()
        return query or 'collectible trading card'
