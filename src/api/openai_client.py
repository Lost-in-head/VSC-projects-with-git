"""
OpenAI API client
Handles image analysis with GPT-4o Vision
"""
import json
import logging
import base64
import time
import requests
from src.config import OPENAI_API_KEY, OPENAI_MODEL, USE_OPENAI_MOCK
from src.api.mock_openai import describe_image_mock

logger = logging.getLogger(__name__)

_OPENAI_TIMEOUT = 60          # seconds — vision requests can be slow
_MAX_RETRIES = 3
_RETRY_BACKOFF = 2.0          # seconds between retries (doubles each attempt)


def describe_image(image_path: str) -> dict:
    """
    Send image to OpenAI Vision and get structured description.
    Falls back to mock if USE_OPENAI_MOCK is True or API key not set.

    Returns:
        dict with either single-item keys (brand/model/...) or
        a multi-item shape: {"cards": [ ... ]} for photos containing several cards.
    """

    # Use mock if enabled or no API key
    if USE_OPENAI_MOCK or not OPENAI_API_KEY:
        logger.info("Using MOCK OpenAI (not consuming API calls)")
        return describe_image_mock(image_path)

    # Read and encode image
    try:
        with open(image_path, "rb") as f:
            img_bytes = f.read()
    except FileNotFoundError:
        logger.warning("Image not found: %s — falling back to mock data", image_path)
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
    Analyze this photo for resale listing generation.

    If there is ONE primary item, return JSON object with:
    - brand, model, category, condition, features, estimated_value_range, grading_notes

    grading_notes must be specific and evidence-based. List visible flaws such as:
    - Whitening on corners
    - Surface scratches
    - Edge wear

    If there are MULTIPLE trading cards visible, return:
    {
      "cards": [
        {
          "brand": "Topps/Panini/etc",
          "model": "Card title",
          "category": "Sports Trading Cards",
          "condition": "Near Mint/Good/etc",
          "features": ["feature1", "feature2"],
          "grading_notes": ["Whitening on corners", "Surface scratches"],
          "estimated_value_range": "$X-Y",
          "player_name": "...",
          "set_name": "...",
          "year": "...",
          "card_number": "...",
          "grade": "Ungraded/PSA 9/etc"
        }
      ]
    }

    Return ONLY valid JSON, no extra text.
    """

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{img_base64}"},
                    },
                ],
            }
        ],
        "max_tokens": 1500,
    }

    last_error = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=_OPENAI_TIMEOUT)
            response.raise_for_status()
            last_error = None
            break
        except Exception as exc:
            last_error = exc
            logger.warning(
                "OpenAI API error (attempt %d/%d): %s", attempt + 1, _MAX_RETRIES, exc
            )
        if attempt < _MAX_RETRIES - 1:
            time.sleep(_RETRY_BACKOFF * (attempt + 1))

    if last_error is not None:
        logger.warning("All OpenAI retries exhausted — falling back to mock data")
        return describe_image_mock(image_path)

    # Parse response
    content = response.json()["choices"][0]["message"]["content"]

    # Try to parse as JSON
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
    except Exception:
        pass

    # Fallback if JSON parsing fails
    logger.warning("Failed to parse OpenAI JSON response — using fallback structure")
    return {
        "brand": "Unknown",
        "model": "Item",
        "category": "Other",
        "condition": "Good",
        "features": [content[:50]],
        "estimated_value_range": "Unknown",
    }
