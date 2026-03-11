"""
Mock OpenAI client for development
Returns realistic dummy data for testing without API keys
"""
import random
from typing import Dict


def describe_image_mock(image_path: str) -> Dict:
    """
    Return mock image analysis data.
    In production, this would call OpenAI Vision API.
    """
    
    # Realistic mock data for testing


    if any(token in image_path.lower() for token in ["multi", "lot", "cards"]):
        return {
            "cards": [
                {
                    "brand": "Topps",
                    "model": "Shohei Ohtani Rookie Card",
                    "category": "Sports Trading Cards",
                    "condition": "Near Mint",
                    "features": ["2018 Topps Update", "Card #US1", "Angels"],
                    "estimated_value_range": "$120-220",
                    "player_name": "Shohei Ohtani",
                    "set_name": "Topps Update",
                    "year": "2018",
                    "card_number": "US1",
                    "grade": "Ungraded",
                },
                {
                    "brand": "Topps",
                    "model": "Aaron Judge Rookie Card",
                    "category": "Sports Trading Cards",
                    "condition": "Very Good",
                    "features": ["2017 Topps", "Card #287", "Yankees"],
                    "estimated_value_range": "$40-90",
                    "player_name": "Aaron Judge",
                    "set_name": "Topps",
                    "year": "2017",
                    "card_number": "287",
                    "grade": "Ungraded",
                }
            ]
        }
    MOCK_ITEMS = [
        {
            "brand": "Apple",
            "model": "MacBook Air M2 2023",
            "category": "Electronics > Computers",
            "condition": "Like New",
            "features": ["13-inch display", "16GB RAM", "256GB SSD", "Silver"],
            "estimated_value_range": "$800-1000"
        },
        {
            "brand": "Sony",
            "model": "WH-1000XM4 Headphones",
            "category": "Electronics > Audio",
            "condition": "Very Good",
            "features": ["Noise cancelling", "Wireless", "30hr battery", "Black"],
            "estimated_value_range": "$250-350"
        },
        {
            "brand": "Canon",
            "model": "EOS R6 DSLR Camera",
            "category": "Photography > Cameras",
            "condition": "Good",
            "features": ["20MP full-frame", "4K video", "Mirrorless", "Body only"],
            "estimated_value_range": "$1500-1800"
        },
        {
            "brand": "Patagonia",
            "model": "Down Jacket",
            "category": "Clothing > Outerwear",
            "condition": "Very Good",
            "features": ["Size Large", "Lightweight", "Blue", "Water resistant"],
            "estimated_value_range": "$100-150"
        },
        {
            "brand": "Dyson",
            "model": "V15 Vacuum",
            "category": "Home & Garden > Cleaning",
            "condition": "Like New",
            "features": ["Cordless", "HEPA filter", "60 min runtime", "Silver"],
            "estimated_value_range": "$400-550"
        },
    ]
    
    # Return a random realistic item
    return random.choice(MOCK_ITEMS)
