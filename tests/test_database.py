"""
Isolated unit tests for the database layer (src/database.py).

Every test uses a fresh in-memory / tmp-path SQLite database so there is
no shared state between tests.
"""
import json
import pytest
import src.database as db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Redirect the module-level DATABASE_PATH to a fresh temp file."""
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "test.db")
    db.init_db()


# ---------------------------------------------------------------------------
# init_db / basic save+retrieve
# ---------------------------------------------------------------------------

def _make_listing(**overrides):
    defaults = dict(
        title="Test Card",
        filename="test.jpg",
        analysis={
            "category": "Sports Trading Cards",
            "condition": "Near Mint",
            "brand": "Topps",
            "model": "Rookie Card",
            "features": ["Serial numbered"],
        },
        comparable_listings=[{"title": "Comp", "price": 25.0, "url": "http://example.com"}],
        suggested_price=25.0,
        payload={"sku": "TEST-SKU", "product": {"title": "Test Card"}},
    )
    defaults.update(overrides)
    return defaults


def test_get_all_listings_empty_initially():
    assert db.get_all_listings() == []


def test_save_listing_returns_integer_id():
    lid = db.save_listing(**_make_listing())
    assert isinstance(lid, int)
    assert lid >= 1


def test_get_all_listings_returns_saved_listings():
    db.save_listing(**_make_listing(title="Card A"))
    db.save_listing(**_make_listing(title="Card B"))
    listings = db.get_all_listings()
    titles = [l["title"] for l in listings]
    assert "Card A" in titles
    assert "Card B" in titles


def test_get_listing_returns_correct_fields():
    lid = db.save_listing(**_make_listing(title="Detailed Card"))
    row = db.get_listing(lid)
    assert row is not None
    assert row["id"] == lid
    assert row["title"] == "Detailed Card"
    assert row["brand"] == "Topps"
    assert row["model"] == "Rookie Card"
    assert row["condition"] == "Near Mint"
    assert isinstance(row["features"], list)
    assert isinstance(row["comparable_listings"], list)
    assert isinstance(row["payload"], dict)
    assert row["status"] == "draft"


def test_get_listing_nonexistent_returns_none():
    assert db.get_listing(99999) is None


# ---------------------------------------------------------------------------
# update_listing_status
# ---------------------------------------------------------------------------

def test_update_listing_status_returns_true_on_success():
    lid = db.save_listing(**_make_listing())
    assert db.update_listing_status(lid, "published") is True
    assert db.get_listing(lid)["status"] == "published"


def test_update_listing_status_returns_false_for_nonexistent():
    assert db.update_listing_status(99999, "published") is False


def test_update_listing_status_archived():
    lid = db.save_listing(**_make_listing())
    db.update_listing_status(lid, "archived")
    assert db.get_listing(lid)["status"] == "archived"


# ---------------------------------------------------------------------------
# delete_listing
# ---------------------------------------------------------------------------

def test_delete_listing_removes_record():
    lid = db.save_listing(**_make_listing())
    assert db.delete_listing(lid) is True
    assert db.get_listing(lid) is None


def test_delete_listing_returns_false_for_nonexistent():
    assert db.delete_listing(99999) is False


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------

def test_get_stats_empty_database():
    stats = db.get_stats()
    assert stats == {"total": 0, "drafts": 0, "published": 0, "archived": 0}


def test_get_stats_counts_correctly():
    db.save_listing(**_make_listing(title="Draft 1"))
    db.save_listing(**_make_listing(title="Draft 2"))
    lid_pub = db.save_listing(**_make_listing(title="Published"))
    lid_arch = db.save_listing(**_make_listing(title="Archived"))

    db.update_listing_status(lid_pub, "published")
    db.update_listing_status(lid_arch, "archived")

    stats = db.get_stats()
    assert stats["total"] == 4
    assert stats["drafts"] == 2
    assert stats["published"] == 1
    assert stats["archived"] == 1


def test_get_stats_includes_archived_key():
    """Regression: stats must always include the 'archived' key."""
    stats = db.get_stats()
    assert "archived" in stats


# ---------------------------------------------------------------------------
# record_publish_result
# ---------------------------------------------------------------------------

def test_record_publish_result_success_sets_status():
    lid = db.save_listing(**_make_listing())
    db.record_publish_result(lid, published=True, external_listing_id="EXT-123")
    row = db.get_listing(lid)
    assert row["status"] == "published"
    assert row["external_listing_id"] == "EXT-123"
    assert row["published_at"] is not None
    assert row["publish_error"] is None


def test_record_publish_result_failure_stores_error():
    lid = db.save_listing(**_make_listing())
    db.record_publish_result(lid, published=False, error_message="upstream timeout")
    row = db.get_listing(lid)
    assert row["status"] == "draft"
    assert "upstream timeout" in row["publish_error"]


def test_record_publish_result_nonexistent_returns_false():
    assert db.record_publish_result(99999, published=True) is False


# ---------------------------------------------------------------------------
# Robustness: corrupt JSON stored in the DB
# ---------------------------------------------------------------------------

def test_get_listing_handles_corrupt_features_json(tmp_path, monkeypatch):
    """get_listing should gracefully degrade when features JSON is corrupt."""
    import sqlite3

    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "corrupt.db")
    db.init_db()
    lid = db.save_listing(**_make_listing())

    # Manually corrupt the features column
    with sqlite3.connect(tmp_path / "corrupt.db") as conn:
        conn.execute("UPDATE listings SET features = 'NOT JSON' WHERE id = ?", (lid,))
        conn.commit()

    row = db.get_listing(lid)
    assert row is not None
    assert row["features"] == []


def test_get_listing_handles_corrupt_comparable_listings_json(tmp_path, monkeypatch):
    """get_listing should gracefully degrade when comparable_listings JSON is corrupt."""
    import sqlite3

    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "corrupt2.db")
    db.init_db()
    lid = db.save_listing(**_make_listing())

    with sqlite3.connect(tmp_path / "corrupt2.db") as conn:
        conn.execute(
            "UPDATE listings SET comparable_listings = 'BAD JSON' WHERE id = ?", (lid,)
        )
        conn.commit()

    row = db.get_listing(lid)
    assert row is not None
    assert row["comparable_listings"] == []


# ---------------------------------------------------------------------------
# save_listing with missing / None analysis fields
# ---------------------------------------------------------------------------

def test_save_listing_with_minimal_analysis():
    lid = db.save_listing(
        title="Minimal",
        filename="x.jpg",
        analysis={},
        comparable_listings=[],
        suggested_price=0.0,
        payload={"sku": "X"},
    )
    assert lid is not None
    row = db.get_listing(lid)
    assert row["brand"] == ""
    assert row["features"] == []
