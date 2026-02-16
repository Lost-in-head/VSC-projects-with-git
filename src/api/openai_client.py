"""
OpenAI API client
Handles image analysis with GPT-4o Vision
"""
import base64
import requests
from src.config import OPENAI_API_KEY, OPENAI_MODEL, USE_OPENAI_MOCK
from src.api.mock_openai import describe_image_mock


def describe_image(image_path: str) -> dict:
    """
    Send image to OpenAI Vision and get structured description.
    Falls back to mock if USE_OPENAI_MOCK is True or API key not set.
    
    Returns:
        dict with keys: brand, model, category, condition, features
    """
    
    # Use mock if enabled or no API key
    if USE_OPENAI_MOCK or not OPENAI_API_KEY:
        print("📝 Using MOCK OpenAI (not consuming API calls)")
        return describe_image_mock(image_path)
    
    # Read and encode image
    try:
        with open(image_path, "rb") as f:
            img_bytes = f.read()
    except FileNotFoundError:
        print(f"❌ Image not found: {image_path}")
        # Fallback to mock
        return describe_image_mock(image_path)
    
    img_base64 = base64.b64encode(img_bytes).decode()
    
    # Determine image type
    if image_path.lower().endswith(".png"):
        media_type = "image/png"
    elif image_path.lower().endswith(".gif"):
        media_type = "image/gif"
    else:
        media_type = "image/jpeg"
    
    # Call OpenAI Vision
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    prompt = """
    Analyze this item photo and provide a structured JSON response with:
    - brand: The brand/manufacturer (or "Unknown")
    - model: Specific model name or description
    - category: eBay category (e.g., "Electronics", "Clothing", "Home & Garden")
    - condition: One of (New, Like New, Very Good, Good, Acceptable)
    - features: List of 3-5 key features visible in the photo
    - estimated_value_range: Rough price estimate (e.g., "$25-50")
    
    Return ONLY valid JSON, no extra text.
    """
    
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{img_base64}"
                        }
                    }
                ],
            }
        ],
        "max_tokens": 300,
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"⚠️  API error: {e}. Falling back to mock data")
        return describe_image_mock(image_path)
    
    # Parse response
    content = response.json()["choices"][0]["message"]["content"]
    
    # Try to parse as JSON
    import json
    try:
        # Find JSON in response (in case of extra text)
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = content[start:end]
            return json.loads(json_str)
    except:
        pass
    
    # Fallback if JSON parsing fails
    return {
        "brand": "Unknown",
        "model": "Item",
        "category": "Other",
        "condition": "Good",
        "features": [content[:50]],
        "estimated_value_range": "Unknown"
    }
