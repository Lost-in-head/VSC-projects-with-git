"""
Main entry point
Orchestrates the image → eBay listing pipeline
"""
import json
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.openai_client import describe_image
from src.api.ebay_client import search_ebay, suggest_price, build_listing_payload

logger = logging.getLogger(__name__)


def main():
    """
    Main pipeline:
    1. Analyze image with OpenAI Vision (or mock)
    2. Search eBay for similar items (or mock)
    3. Suggest price based on comparable listings
    4. Build listing payload
    """

    # TODO: Replace with actual image path
    image_path = "sample_item.jpg"

    logger.info("=" * 70)
    logger.info("eBay Listing Generator (Mock Mode - Dev Testing)")
    logger.info("=" * 70)

    # Step 1: Analyze image
    logger.info("Step 1: Analyzing image...")
    try:
        analysis = describe_image(image_path)
        logger.info(
            "Title: %s %s | Condition: %s | Category: %s | Features: %s",
            analysis.get("brand", "Unknown"),
            analysis.get("model", "Item"),
            analysis.get("condition", "Unknown"),
            analysis.get("category", "Unknown"),
            ", ".join(analysis.get("features", [])),
        )
    except FileNotFoundError:
        logger.warning("Image not found: %s — using demo data instead.", image_path)
        analysis = {
            "brand": "Demo Brand",
            "model": "Demo Product",
            "category": "Electronics",
            "condition": "Like New",
            "features": ["Feature 1", "Feature 2", "Feature 3"],
            "estimated_value_range": "$100-200",
        }
    except Exception as e:
        logger.error("Image analysis failed: %s", e)
        return

    # Step 2: Search eBay
    logger.info("Step 2: Searching eBay for similar items...")
    try:
        query = f"{analysis.get('brand', '')} {analysis.get('model', '')}"
        listings = search_ebay(query.strip(), limit=5)

        if listings:
            logger.info("Found %d similar listings:", len(listings))
            for i, listing in enumerate(listings, 1):
                logger.info("  %d. %-50s | $%.2f", i, listing["title"], listing["price"])
        else:
            logger.warning("No similar listings found")
    except Exception as e:
        logger.error("eBay search failed: %s", e)
        listings = []

    # Step 3: Suggest price
    logger.info("Step 3: Calculating suggested price...")
    price = suggest_price(listings)
    if price is not None and price > 0:
        logger.info("Suggested price: $%.2f", price)
    else:
        price = 50.00  # Default fallback
        logger.warning("Using placeholder price: $%.2f", price)

    # Step 4: Build listing payload
    logger.info("Step 4: Building listing payload...")
    title = f"{analysis.get('brand', 'Item')} {analysis.get('model', '')}"
    description = (
        f"Category: {analysis.get('category', 'Other')}\n"
        f"Condition: {analysis.get('condition', 'Good')}\n\nFeatures:\n"
    )
    for feature in analysis.get("features", []):
        description += f"- {feature}\n"

    payload = build_listing_payload(
        title, description, price, condition=analysis.get("condition", "USED_GOOD")
    )

    logger.info("Draft eBay Listing (JSON):\n%s", json.dumps(payload, indent=2))
    logger.info("=" * 70)
    logger.info("Success! Your listing draft is ready.")
    logger.info("Next: Review above and update .env with real API keys to publish")
    logger.info("=" * 70)

    return payload


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    main()
