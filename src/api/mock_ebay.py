"""
Mock eBay client for development
Returns realistic dummy data for testing without API credentials
"""
import random
from typing import List, Dict, Optional


def search_ebay_mock(query: str, limit: int = 5) -> List[Dict]:
    """
    Return mock eBay search results.
    In production, this would call eBay Finding API.
    """
    
    # Realistic mock pricing data for testing
    MOCK_LISTINGS = {
        "electronics": [
            {"title": "Laptop 13\" i7 16GB RAM", "price": 650.00},
            {"title": "Laptop 13\" i7 512GB SSD", "price": 720.00},
            {"title": "Laptop 13\" Intel Core i7", "price": 695.00},
            {"title": "Laptop 13 inch Silver", "price": 750.00},
            {"title": "Computer Portable 13\"", "price": 680.00},
        ],
        "audio": [
            {"title": "Wireless Over Ear Headphones", "price": 280.00},
            {"title": "Noise Cancelling Headphones Black", "price": 265.00},
            {"title": "Premium Audio Headphones", "price": 295.00},
            {"title": "Noise Cancel Headphones", "price": 275.00},
            {"title": "Wireless Headphones Premium", "price": 320.00},
        ],
        "camera": [
            {"title": "Mirrorless Camera Full Frame", "price": 1600.00},
            {"title": "DSLR Camera Professional", "price": 1750.00},
            {"title": "Digital Camera Mirrorless", "price": 1650.00},
            {"title": "Full Frame Mirrorless Camera", "price": 1550.00},
            {"title": "Camera 4K Mirrorless", "price": 1700.00},
        ],
        "clothing": [
            {"title": "Down Jacket Winter Coat", "price": 125.00},
            {"title": "Waterproof Jacket Outdoor", "price": 135.00},
            {"title": "Puffer Jacket Blue", "price": 110.00},
            {"title": "Winter Down Jacket", "price": 140.00},
            {"title": "Insulated Jacket Breathable", "price": 130.00},
        ],
        "vacuum": [
            {"title": "Cordless Vacuum Cleaner", "price": 480.00},
            {"title": "Powerful Cordless Stick Vacuum", "price": 520.00},
            {"title": "Vacuum Cordless Handheld", "price": 450.00},
            {"title": "Digital Cordless Vacuum", "price": 500.00},
            {"title": "Wireless Vacuum Cleaner Pro", "price": 490.00},
        ]
    }
    
    # Determine category from query
    query_lower = query.lower()
    if any(word in query_lower for word in ["laptop", "computer", "macbook", "intel"]):
        category = "electronics"
    elif any(word in query_lower for word in ["headphone", "audio", "speaker"]):
        category = "audio"
    elif any(word in query_lower for word in ["camera", "dslr", "mirrorless"]):
        category = "camera"
    elif any(word in query_lower for word in ["jacket", "coat", "clothing"]):
        category = "clothing"
    elif any(word in query_lower for word in ["vacuum", "cleaner"]):
        category = "vacuum"
    else:
        category = random.choice(list(MOCK_LISTINGS.keys()))
    
    # Get mock listings
    listings = MOCK_LISTINGS.get(category, MOCK_LISTINGS["electronics"])
    
    # Return requested number of results
    results = []
    for i in range(min(limit, len(listings))):
        entry = listings[i]
        results.append({
            "title": entry["title"],
            "price": entry["price"],
            "url": f"https://www.ebay.com/itm/mock-{i}"
        })
    
    return results


def suggest_price_mock(listings: List[Dict]) -> Optional[float]:
    """
    Calculate suggested price from mock listings (median).
    """
    if not listings:
        return None
    prices = [l["price"] for l in listings]
    prices.sort()
    n = len(prices)
    if n % 2 == 0:
        return round((prices[n//2 - 1] + prices[n//2]) / 2, 2)
    else:
        return float(prices[n // 2])


def build_listing_payload_mock(title: str, description: str, price: float, condition: str = "USED_GOOD") -> Dict:
    """
    Build mock eBay listing payload (simplified).
    """
    return {
        "sku": f"MOCK_SKU_{random.randint(100000, 999999)}",
        "product": {
            "title": title[:80],
            "description": description,
        },
        "availability": {
            "shipToLocationAvailability": {
                "quantity": 1
            }
        },
        "price": {
            "value": str(price),
            "currency": "USD"
        },
        "condition": condition,
    }
