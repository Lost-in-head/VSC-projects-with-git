import pytest

from src.app import create_app


@pytest.fixture
def client():
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
