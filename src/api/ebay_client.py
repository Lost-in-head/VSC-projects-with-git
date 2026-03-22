"""
eBay API client
Handles eBay Finding and Sell APIs
Falls back to mock data if credentials not available
"""
import base64
import json
import uuid
import requests
from statistics import median
from src.utils.helpers import clean_title
from src.config import (
    EBAY_CLIENT_ID,
    EBAY_CLIENT_SECRET,
    EBAY_SANDBOX,
    EBAY_OAUTH_ENDPOINT,
    EBAY_API_ENDPOINT,
    USE_EBAY_MOCK,
)
from src.api.mock_ebay import search_ebay_mock


def get_ebay_token() -> str:
    """
    Obtain OAuth token from eBay (client credentials flow).
    """
    if not EBAY_CLIENT_ID or not EBAY_CLIENT_SECRET:
        raise ValueError("eBay credentials not set")
    
    auth_str = f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }
    
    response = requests.post(EBAY_OAUTH_ENDPOINT, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def search_ebay(query: str, limit: int = 5) -> list:
    """
    Search eBay using Finding API.
    Falls back to mock if credentials missing or USE_EBAY_MOCK is True.
    
    Returns:
        List of dicts: {title, price, url}
    """
    
    # Use mock if enabled or no credentials
    if USE_EBAY_MOCK or not EBAY_CLIENT_ID or not EBAY_CLIENT_SECRET:
        print("📝 Using MOCK eBay search (not consuming API calls)")
        return search_ebay_mock(query, limit)
    
    try:
        finding_endpoint = (
            "https://svcs.sandbox.ebay.com/services/search/FindingService/v1"
            if EBAY_SANDBOX
            else "https://svcs.ebay.com/services/search/FindingService/v1"
        )
        
        params = {
            "OPERATION-NAME": "findItemsByKeywords",
            "SERVICE-VERSION": "1.13.0",
            "SECURITY-APPNAME": EBAY_CLIENT_ID,
            "RESPONSE-DATA-FORMAT": "JSON",
            "keywords": query,
            "paginationInput.entriesPerPage": limit,
            "outputSelector": "SellerInfo",
        }
        
        response = requests.get(finding_endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        try:
            items = data["findItemsByKeywordsResponse"][0]["searchResult"][0]["item"]
            for item in items:
                price = float(item["sellingStatus"][0]["currentPrice"][0]["__value__"])
                title = item["title"][0]
                url = item["viewItemURL"][0]
                results.append({
                    "title": title,
                    "price": price,
                    "url": url
                })
        except (KeyError, IndexError):
            pass
        
        return results
    except Exception as e:
        print(f"⚠️  eBay API error: {e}. Falling back to mock data")
        return search_ebay_mock(query, limit)


def suggest_price(listings: list) -> float:
    """Calculate suggested price from comparable listings (median)."""
    if not listings:
        return None
    prices = [l["price"] for l in listings if "price" in l]
    if not prices:
        return None
    return round(median(prices), 2)


def build_listing_payload(title: str, description: str, price: float, condition: str = "USED_GOOD") -> dict:
    """
    Build eBay Sell Inventory API payload (simplified).
    Each call generates a unique SKU so multiple listings never collide.
    """
    sku = f"LISTING-{uuid.uuid4().hex[:12].upper()}"
    return {
        "sku": sku,
        "product": {
            "title": clean_title(title, max_length=80),
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



def publish_listing(payload: dict) -> dict:
    """Publish listing payload to eBay (mock or real)."""
    if USE_EBAY_MOCK or not EBAY_CLIENT_ID or not EBAY_CLIENT_SECRET:
        sku = payload.get("sku", "AUTO_GENERATED_SKU")
        return {
            "status": "published",
            "external_listing_id": f"MOCK-{sku}",
            "mode": "mock",
        }

    token = get_ebay_token()
    endpoint = f"{EBAY_API_ENDPOINT}/sell/inventory/v1/inventory_item/{payload['sku']}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Content-Language": "en-US",
    }

    response = requests.put(endpoint, headers=headers, json=payload, timeout=15)
    response.raise_for_status()

    return {
        "status": "published",
        "external_listing_id": payload["sku"],
        "mode": "real",
    }
