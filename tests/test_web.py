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


# ---------------------------------------------------------------------------
# Additional edge-case / new-feature tests
# ---------------------------------------------------------------------------

def test_upload_with_no_photo_field_returns_400(client):
    """POST /api/upload with no file field should return 400."""
    response = client.post('/api/upload', data={}, content_type='multipart/form-data')
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_upload_with_empty_filename_returns_400(client):
    """POST /api/upload with an empty filename should return 400."""
    import io
    data = {'photo': (io.BytesIO(b'data'), '')}
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 400


def test_upload_disallowed_extension_returns_400(client):
    """POST /api/upload with a .exe file should return 400."""
    import io
    data = {'photo': (io.BytesIO(b'MZ'), 'malware.exe')}
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_update_status_to_archived(client):
    """PATCH to 'archived' should succeed for an existing listing."""
    lid = db.save_listing(
        title='Archivable',
        filename='x.jpg',
        analysis={'brand': 'Topps', 'condition': 'Good', 'features': []},
        comparable_listings=[],
        suggested_price=5.0,
        payload={'sku': 'X'},
    )
    response = client.patch(f'/api/listings/{lid}/status', json={'status': 'archived'})
    assert response.status_code == 200
    listing = db.get_listing(lid)
    assert listing['status'] == 'archived'


def test_stats_endpoint_includes_archived_field(client):
    """The index route stats must include the 'archived' count."""
    lid = db.save_listing(
        title='Arch',
        filename='a.jpg',
        analysis={'brand': 'A', 'condition': 'Good', 'features': []},
        comparable_listings=[],
        suggested_price=1.0,
        payload={'sku': 'A'},
    )
    db.update_listing_status(lid, 'archived')

    # get_stats is called by the index route; also test it directly
    stats = db.get_stats()
    assert 'archived' in stats
    assert stats['archived'] >= 1


def test_publish_already_published_listing_returns_409(client):
    """Attempting to publish an already-published listing should return 409."""
    lid = db.save_listing(
        title='Already Published',
        filename='p.jpg',
        analysis={'brand': 'B', 'condition': 'Good', 'features': []},
        comparable_listings=[],
        suggested_price=10.0,
        payload={'sku': 'P'},
    )
    db.record_publish_result(lid, published=True, external_listing_id='EXT-P')

    response = client.post(f'/api/listings/{lid}/publish')
    assert response.status_code == 409


def test_delete_existing_listing(client):
    """DELETE on an existing listing should return 200."""
    lid = db.save_listing(
        title='To Delete',
        filename='d.jpg',
        analysis={'brand': 'D', 'condition': 'Good', 'features': []},
        comparable_listings=[],
        suggested_price=3.0,
        payload={'sku': 'D'},
    )
    response = client.delete(f'/api/listings/{lid}')
    assert response.status_code == 200
    assert db.get_listing(lid) is None


def test_download_file_not_found(client):
    """GET /downloads/<missing> should return 404."""
    response = client.get('/downloads/nonexistent_file_xyz.jpg')
    assert response.status_code == 404


def test_get_listings_returns_list_sorted_newest_first(client):
    """Listings should be ordered newest first."""
    db.save_listing(
        title='First',
        filename='f1.jpg',
        analysis={'brand': 'A', 'features': []},
        comparable_listings=[],
        suggested_price=1.0,
        payload={'sku': 'S1'},
    )
    db.save_listing(
        title='Second',
        filename='f2.jpg',
        analysis={'brand': 'B', 'features': []},
        comparable_listings=[],
        suggested_price=2.0,
        payload={'sku': 'S2'},
    )
    response = client.get('/api/listings')
    data = response.get_json()
    assert response.status_code == 200
    titles = [l['title'] for l in data]
    assert titles[0] == 'Second'  # newest first
