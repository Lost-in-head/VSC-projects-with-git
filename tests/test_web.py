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
    import io
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
