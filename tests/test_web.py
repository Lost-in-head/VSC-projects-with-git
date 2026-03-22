import io
import json
import pytest

from src.app import create_app
import src.database as db


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "test_listings.db")
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_index_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"eBay Listing Generator" in response.data


def test_get_listings_api(client):
    response = client.get("/api/listings")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_update_status_missing_listing_returns_404(client):
    response = client.patch("/api/listings/999/status", json={"status": "published"})
    assert response.status_code == 404


def test_delete_missing_listing_returns_404(client):
    response = client.delete("/api/listings/999")
    assert response.status_code == 404


def test_update_status_handles_empty_json_body(client):
    # should default to draft and return 404 for missing listing instead of 500
    response = client.patch(
        "/api/listings/999/status",
        data="",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 404


def test_upload_returns_500_on_processing_failure(client, monkeypatch):
    """upload_file should return HTTP 500 when the listing pipeline fails."""
    monkeypatch.setattr('src.app.process_listing', lambda path, filename: {
        'success': False,
        'error': 'mock pipeline failure',
        'message': '❌ Failed to generate listing',
    })
    data = {'photo': (io.BytesIO(b'fake image data'), 'test.jpg')}
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 500
    assert response.get_json()['success'] is False



def test_publish_listing_not_found_returns_404(client):
    response = client.post('/api/listings/999/publish')
    assert response.status_code == 404


def test_publish_listing_happy_path(client, monkeypatch):
    listing_id = db.save_listing(
        title='Draft Listing',
        filename='sample.jpg',
        analysis={
            'category': 'Electronics',
            'condition': 'Used',
            'brand': 'Sony',
            'model': 'WH-1000XM4',
            'features': ['Noise Canceling'],
        },
        comparable_listings=[{'title': 'Comp', 'price': 100.0, 'url': 'u'}],
        suggested_price=100.0,
        payload={'sku': 'AUTO_GENERATED_SKU', 'product': {'title': 'Draft Listing'}},
    )

    monkeypatch.setattr('src.app.publish_listing', lambda payload: {
        'status': 'published',
        'external_listing_id': 'MOCK-AUTO_GENERATED_SKU',
    })

    response = client.post(f'/api/listings/{listing_id}/publish')
    data = response.get_json()

    assert response.status_code == 200
    assert data['success'] is True
    assert data['external_listing_id'] == 'MOCK-AUTO_GENERATED_SKU'

    listing = db.get_listing(listing_id)
    assert listing['status'] == 'published'
    assert listing['external_listing_id'] == 'MOCK-AUTO_GENERATED_SKU'
    assert listing['published_at'] is not None


def test_publish_listing_failure_records_error(client, monkeypatch):
    listing_id = db.save_listing(
        title='Draft Listing',
        filename='sample.jpg',
        analysis={'category': 'Electronics', 'condition': 'Used', 'brand': 'Sony', 'model': 'WH-1000XM4', 'features': []},
        comparable_listings=[],
        suggested_price=100.0,
        payload={'sku': 'AUTO_GENERATED_SKU', 'product': {'title': 'Draft Listing'}},
    )

    def raise_publish(_payload):
        raise RuntimeError('upstream unavailable')

    monkeypatch.setattr('src.app.publish_listing', raise_publish)

    response = client.post(f'/api/listings/{listing_id}/publish')
    assert response.status_code == 502

    listing = db.get_listing(listing_id)
    assert listing['status'] == 'draft'
    assert 'upstream unavailable' in listing['publish_error']


def test_update_status_invalid_value_returns_400(client):
    """PATCH with an unrecognised status value should return 400."""
    response = client.patch('/api/listings/999/status', json={'status': 'banana'})
    assert response.status_code == 400


def test_upload_413_handler(client):
    """Flask's MAX_CONTENT_LENGTH handler should return 413 with a JSON error."""
    # Simulate the 413 handler directly via the app error handler
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
        with app.test_request_context():
            from werkzeug.exceptions import RequestEntityTooLarge
            response = app.make_response(app.handle_http_exception(RequestEntityTooLarge()))
    assert response.status_code == 413
    data = json.loads(response.get_data())
    assert 'error' in data


def test_get_listing_detail_returns_200_with_expected_fields(client):
    """GET /api/listings/<id> for a real saved listing should return 200 and all fields."""
    listing_id = db.save_listing(
        title='Test Card',
        filename='test.jpg',
        analysis={
            'category': 'Sports Trading Cards',
            'condition': 'Near Mint',
            'brand': 'Topps',
            'model': 'Rookie Card',
            'features': ['Serial numbered'],
        },
        comparable_listings=[{'title': 'Comp', 'price': 25.0, 'url': 'http://example.com'}],
        suggested_price=25.0,
        payload={'sku': 'TEST-SKU', 'product': {'title': 'Test Card'}},
    )

    response = client.get(f'/api/listings/{listing_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == listing_id
    assert data['title'] == 'Test Card'
    assert data['brand'] == 'Topps'
    assert data['model'] == 'Rookie Card'
    assert data['condition'] == 'Near Mint'
    assert isinstance(data['features'], list)
    assert isinstance(data['comparable_listings'], list)
    assert 'payload' in data
    assert 'suggested_price' in data
    assert 'status' in data


def test_get_listing_detail_missing_returns_404(client):
    """GET /api/listings/<id> for a nonexistent listing should return 404."""
    response = client.get('/api/listings/99999')
    assert response.status_code == 404
