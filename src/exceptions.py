"""
Custom exceptions for Cards-4-Sale.
Provides semantic error handling with context.
"""


class CardsForSaleException(Exception):
    """Base exception for all Cards-4-Sale errors."""


class ImageAnalysisError(CardsForSaleException):
    """Raised when image analysis fails."""

    def __init__(self, image_path: str, reason: str, original_error: Exception = None):
        self.image_path = image_path
        self.reason = reason
        self.original_error = original_error
        super().__init__(f"Image analysis failed for {image_path}: {reason}")


class EbayAPIError(CardsForSaleException):
    """Raised when an eBay API call fails."""

    def __init__(self, operation: str, query: str = None, reason: str = None):
        self.operation = operation
        self.query = query
        self.reason = reason
        msg = f"eBay {operation} failed"
        if query:
            msg += f" for '{query}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class OpenAIAPIError(CardsForSaleException):
    """Raised when an OpenAI API call fails."""

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"OpenAI {operation} failed: {reason}")


class DatabaseError(CardsForSaleException):
    """Raised when a database operation fails."""

    def __init__(self, operation: str, reason: str, original_error: Exception = None):
        self.operation = operation
        self.reason = reason
        self.original_error = original_error
        super().__init__(f"Database {operation} failed: {reason}")


class ListingGenerationError(CardsForSaleException):
    """Raised when listing generation fails."""

    def __init__(self, stage: str, reason: str, original_error: Exception = None):
        self.stage = stage
        self.reason = reason
        self.original_error = original_error
        super().__init__(f"Listing generation failed at {stage}: {reason}")


class ValidationError(CardsForSaleException):
    """Raised when input validation fails."""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"Validation failed for {field}: {reason}")
