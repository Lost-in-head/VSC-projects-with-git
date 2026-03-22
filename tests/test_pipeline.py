from src.main import main
from src.app import process_listing


def test_full_cli_pipeline(monkeypatch, capsys):
    monkeypatch.setenv("USE_OPENAI_MOCK", "True")
    monkeypatch.setenv("USE_EBAY_MOCK", "True")
    payload = main()
    assert payload is not None

    captured = capsys.readouterr()
    assert "Success! Your listing draft is ready" in captured.out


def test_process_listing_title_includes_brand_and_model(monkeypatch):
    monkeypatch.setattr("src.app.describe_image", lambda _p: {
        "brand": "Sony",
        "model": "WH-1000XM4",
        "category": "Electronics",
        "condition": "Like New",
        "features": ["Noise Canceling"],
    })
    monkeypatch.setattr("src.app.search_ebay", lambda _q, limit=5: [{"title": "x", "price": 100.0, "url": "u"}])
    monkeypatch.setattr("src.app.suggest_price", lambda _l: 100.0)

    captured = {}

    def fake_build_listing_payload(title, description, price, condition="USED_GOOD"):
        captured["title"] = title
        return {"product": {"title": title}, "price": {"value": str(price)}, "condition": condition}

    monkeypatch.setattr("src.app.build_listing_payload", fake_build_listing_payload)
    monkeypatch.setattr("src.app.save_listing", lambda **kwargs: 1)

    result = process_listing("fake.jpg", "fake.jpg")
    assert result["success"] is True
    assert captured["title"] == "Sony WH-1000XM4"


def test_process_listing_multi_card_photo(monkeypatch):
    monkeypatch.setattr("src.app.describe_image", lambda _p: {
        "cards": [
            {
                "brand": "Topps",
                "model": "Shohei Ohtani Rookie Card",
                "category": "Sports Trading Cards",
                "condition": "Near Mint",
                "features": ["Card #US1"],
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
                "features": ["Card #287"],
                "player_name": "Aaron Judge",
                "set_name": "Topps",
                "year": "2017",
                "card_number": "287",
                "grade": "Ungraded",
            },
        ]
    })

    monkeypatch.setattr("src.app.search_ebay", lambda _q, limit=8: [{"title": "x", "price": 100.0, "url": "u"}])
    monkeypatch.setattr("src.app.suggest_price", lambda _l: 100.0)
    monkeypatch.setattr("src.app.build_listing_payload", lambda title, description, price, condition="USED_GOOD": {"product": {"title": title}, "price": {"value": str(price)}, "condition": condition})

    counter = {'n': 0}
    def fake_save_listing(**kwargs):
        counter['n'] += 1
        return counter['n']

    monkeypatch.setattr("src.app.save_listing", fake_save_listing)

    result = process_listing("multi_cards.jpg", "multi_cards.jpg")
    assert result["success"] is True
    assert result["mode"] == "multi_card"
    assert result["cards_detected"] == 2
    assert len(result["card_results"]) == 2


def test_process_listing_high_value_flag(monkeypatch):
    monkeypatch.setattr('src.app.describe_image', lambda _p: {
        'brand': 'Topps',
        'model': 'Premium Card',
        'category': 'Sports Trading Cards',
        'condition': 'Near Mint',
        'features': ['Serial numbered'],
        'grading_notes': ['Minor corner whitening'],
    })
    monkeypatch.setattr('src.app.search_ebay', lambda _q, limit=8: [{'title': 'x', 'price': 35.0, 'url': 'u'}])
    monkeypatch.setattr('src.app.suggest_price', lambda _l: 35.0)
    monkeypatch.setattr('src.app.build_listing_payload', lambda title, description, price, condition='USED_GOOD': {'product': {'title': title}, 'price': {'value': str(price)}, 'condition': condition})
    monkeypatch.setattr('src.app.save_listing', lambda **kwargs: 1)

    result = process_listing('premium.jpg', 'premium.jpg')
    assert result['success'] is True
    assert result['is_high_value'] is True
    assert result['high_value_threshold'] == 20.0


def test_process_listing_low_value_flag(monkeypatch):
    monkeypatch.setattr('src.app.describe_image', lambda _p: {
        'brand': 'Topps',
        'model': 'Common Card',
        'category': 'Sports Trading Cards',
        'condition': 'Good',
        'features': ['Base card'],
        'grading_notes': ['Visible edge wear'],
    })
    monkeypatch.setattr('src.app.search_ebay', lambda _q, limit=8: [{'title': 'x', 'price': 12.0, 'url': 'u'}])
    monkeypatch.setattr('src.app.suggest_price', lambda _l: 12.0)
    monkeypatch.setattr('src.app.build_listing_payload', lambda title, description, price, condition='USED_GOOD': {'product': {'title': title}, 'price': {'value': str(price)}, 'condition': condition})
    monkeypatch.setattr('src.app.save_listing', lambda **kwargs: 1)

    result = process_listing('cheap.jpg', 'cheap.jpg')
    assert result['success'] is True
    assert result['is_high_value'] is False
