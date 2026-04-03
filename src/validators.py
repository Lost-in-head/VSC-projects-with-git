"""
Input validation for uploaded files and API payloads.
Validates early to prevent bad data from entering the system.
"""
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class ImageValidator:
    """Validates uploaded image files."""

    ALLOWED_TYPES = {'jpg', 'jpeg', 'png', 'gif'}
    MAX_SIZE_BYTES = 16 * 1024 * 1024  # 16 MB
    MAX_FILENAME_LENGTH = 256
    FORBIDDEN_CHARS = {'\x00', '/', '\\'}

    @staticmethod
    def validate_upload(filename: str, file_size: int) -> Tuple[bool, str]:
        """
        Validate uploaded file metadata.

        Returns:
            (is_valid, error_message)
        """
        if not filename:
            return False, "Filename is empty"

        if len(filename) > ImageValidator.MAX_FILENAME_LENGTH:
            return False, f"Filename too long (max {ImageValidator.MAX_FILENAME_LENGTH} chars)"

        if any(char in filename for char in ImageValidator.FORBIDDEN_CHARS):
            return False, "Filename contains forbidden characters"

        try:
            ext = filename.rsplit('.', 1)[1].lower()
        except IndexError:
            return False, "Filename has no extension"

        if ext not in ImageValidator.ALLOWED_TYPES:
            return False, (
                f"Unsupported file type: {ext}. "
                f"Allowed: {', '.join(sorted(ImageValidator.ALLOWED_TYPES))}"
            )

        if file_size == 0:
            return False, "File is empty"

        if file_size > ImageValidator.MAX_SIZE_BYTES:
            size_mb = file_size / 1024 / 1024
            return False, f"File too large: {size_mb:.1f}MB (max 16MB)"

        return True, ""

    @staticmethod
    def validate_mime_type(mime_type: str) -> bool:
        """Return True if the MIME type is an accepted image type."""
        return mime_type in {'image/jpeg', 'image/png', 'image/gif'}


class ListingValidator:
    """Validates generated eBay listing payloads."""

    MIN_PRICE = 0.99
    MAX_PRICE = 100_000.00
    MAX_TITLE_LENGTH = 80
    MAX_DESCRIPTION_LENGTH = 5_000

    VALID_CONDITIONS = {
        'NEW', 'REFURBISHED', 'USED_LIKE_NEW', 'USED_GOOD',
        'USED_ACCEPTABLE', 'NOT_SPECIFIED',
    }

    @staticmethod
    def validate_payload(payload: dict) -> Tuple[bool, str]:
        """
        Validate an eBay listing payload before saving.

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(payload, dict):
            return False, "Payload must be a dictionary"

        if 'sku' not in payload:
            return False, "Missing SKU"

        product = payload.get('product')
        if not isinstance(product, dict):
            return False, "Missing or invalid product section"

        title = product.get('title', '').strip()
        if not title:
            return False, "Title is required"
        if len(title) > ListingValidator.MAX_TITLE_LENGTH:
            return False, (
                f"Title too long (max {ListingValidator.MAX_TITLE_LENGTH} chars, "
                f"got {len(title)})"
            )

        description = product.get('description', '')
        if description and len(description) > ListingValidator.MAX_DESCRIPTION_LENGTH:
            return False, (
                f"Description too long (max {ListingValidator.MAX_DESCRIPTION_LENGTH} chars)"
            )

        price_data = payload.get('price')
        if not price_data:
            return False, "Missing price"

        price_value = price_data.get('value')
        if price_value is None:
            return False, "Missing price value"

        try:
            price_float = float(price_value)
        except (ValueError, TypeError) as exc:
            return False, f"Invalid price format: {exc}"

        if not (ListingValidator.MIN_PRICE <= price_float <= ListingValidator.MAX_PRICE):
            return False, (
                f"Price {price_float} out of range "
                f"(${ListingValidator.MIN_PRICE} - ${ListingValidator.MAX_PRICE})"
            )

        currency = price_data.get('currency', 'USD')
        if currency != 'USD':
            return False, f"Only USD currency supported (got {currency})"

        condition = payload.get('condition', 'USED_GOOD')
        if condition not in ListingValidator.VALID_CONDITIONS:
            return False, f"Invalid condition: {condition}"

        return True, ""


class AnalysisValidator:
    """Validates image analysis results from OpenAI."""

    REQUIRED_FIELDS = {'brand', 'model', 'category', 'condition'}

    @staticmethod
    def validate_analysis(analysis: dict) -> Tuple[bool, str]:
        """Validate an image analysis structure."""
        if not isinstance(analysis, dict):
            return False, "Analysis must be a dictionary"

        if 'cards' in analysis:
            if not isinstance(analysis['cards'], list):
                return False, "Cards must be a list"
            if not analysis['cards']:
                return False, "Cards list is empty"
            for i, card in enumerate(analysis['cards']):
                ok, err = AnalysisValidator._validate_single(card)
                if not ok:
                    return False, f"Card {i}: {err}"
        else:
            ok, err = AnalysisValidator._validate_single(analysis)
            if not ok:
                return False, err

        return True, ""

    @staticmethod
    def _validate_single(item: dict) -> Tuple[bool, str]:
        """Validate a single item/card analysis dict."""
        for field in AnalysisValidator.REQUIRED_FIELDS:
            if field not in item:
                return False, f"Missing required field: {field}"
            value = item[field]
            if not isinstance(value, str) or not value.strip():
                return False, f"Field '{field}' is empty or not a string"

        features = item.get('features')
        if features is not None and not isinstance(features, (list, str)):
            return False, "Features must be a list or string"

        estimated = item.get('estimated_value_range')
        if estimated is not None and not isinstance(estimated, str):
            return False, "estimated_value_range must be a string"

        return True, ""
