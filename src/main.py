"""
Main entry point
Orchestrates the image → eBay listing pipeline
"""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.openai_client import describe_image
from src.api.ebay_client import search_ebay, suggest_price, build_listing_payload


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
    
    print("=" * 70)
    print("📷 eBay Listing Generator (Mock Mode - Dev Testing)")
    print("=" * 70)
    
    # Step 1: Analyze image
    print("\n🔍 Step 1: Analyzing image...")
    try:
        analysis = describe_image(image_path)
        print(f"✓ Title: {analysis.get('brand', 'Unknown')} {analysis.get('model', 'Item')}")
        print(f"  Condition: {analysis.get('condition', 'Unknown')}")
        print(f"  Category: {analysis.get('category', 'Unknown')}")
        print(f"  Features: {', '.join(analysis.get('features', []))}")
    except FileNotFoundError:
        print(f"❌ Image not found: {image_path}")
        print("   Tip: This is normal in mock mode. Using demo data instead.")
        analysis = {
            "brand": "Demo Brand",
            "model": "Demo Product",
            "category": "Electronics",
            "condition": "Like New",
            "features": ["Feature 1", "Feature 2", "Feature 3"],
            "estimated_value_range": "$100-200"
        }
    except Exception as e:
        print(f"❌ Image analysis failed: {e}")
        return
    
    # Step 2: Search eBay
    print("\n🛒 Step 2: Searching eBay for similar items...")
    try:
        # Use brand + model as search query
        query = f"{analysis.get('brand', '')} {analysis.get('model', '')}"
        listings = search_ebay(query.strip(), limit=5)
        
        if listings:
            print(f"✓ Found {len(listings)} similar listings:")
            for i, listing in enumerate(listings, 1):
                print(f"  {i}. {listing['title']:<50} | ${listing['price']:.2f}")
        else:
            print("⚠️  No similar listings found")
    except Exception as e:
        print(f"❌ eBay search failed: {e}")
        listings = []
    
    # Step 3: Suggest price
    print("\n💰 Step 3: Calculating suggested price...")
    price = suggest_price(listings)
    if price > 0:
        print(f"✓ Suggested price: ${price:.2f}")
    else:
        price = 50.00  # Default fallback
        print(f"⚠️  Using placeholder price: ${price:.2f}")
    
    # Step 4: Build listing payload
    print("\n📦 Step 4: Building listing payload...")
    title = f"{analysis.get('brand', 'Item')} {analysis.get('model', '')}"
    description = f"Category: {analysis.get('category', 'Other')}\nCondition: {analysis.get('condition', 'Good')}\n\nFeatures:\n"
    for feature in analysis.get('features', []):
        description += f"- {feature}\n"
    
    payload = build_listing_payload(title, description, price, condition=analysis.get('condition', 'USED_GOOD'))
    
    print("\n✓ Draft eBay Listing (JSON):")
    print(json.dumps(payload, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Success! Your listing draft is ready.")
    print("   Next: Review above and update .env with real API keys to publish")
    print("=" * 70)
    
    return payload


if __name__ == "__main__":
    main()
