"""
Database models and operations for managing eBay listings
"""

import sqlite3
import json
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent / "listings.db"


def init_db():
    """Initialize database with listings table"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                filename TEXT,
                category TEXT,
                condition TEXT,
                brand TEXT,
                model TEXT,
                features TEXT,
                suggested_price REAL,
                comparable_listings TEXT,
                payload TEXT NOT NULL,
                status TEXT DEFAULT 'draft',
                external_listing_id TEXT,
                published_at TIMESTAMP,
                publish_error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )

        # Backfill publish-tracking columns for older DBs
        cursor.execute("PRAGMA table_info(listings)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        if "external_listing_id" not in existing_columns:
            cursor.execute("ALTER TABLE listings ADD COLUMN external_listing_id TEXT")
        if "published_at" not in existing_columns:
            cursor.execute("ALTER TABLE listings ADD COLUMN published_at TIMESTAMP")
        if "publish_error" not in existing_columns:
            cursor.execute("ALTER TABLE listings ADD COLUMN publish_error TEXT")

        conn.commit()


def save_listing(title, filename, analysis, comparable_listings, suggested_price, payload):
    """Save a generated listing to database"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute(
                '''
                INSERT INTO listings
                (title, filename, category, condition, brand, model, features,
                 suggested_price, comparable_listings, payload, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    title,
                    filename,
                    analysis.get("category", ""),
                    analysis.get("condition", ""),
                    analysis.get("brand", ""),
                    analysis.get("model", ""),
                    json.dumps(analysis.get("features", [])),
                    suggested_price,
                    json.dumps(comparable_listings),
                    json.dumps(payload),
                    "draft",
                ),
            )

            listing_id = cursor.lastrowid
            conn.commit()
            return listing_id
    except Exception as e:
        print(f"Error saving listing: {e}")
        return None


def get_all_listings():
    """Get all listings from database"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute(
                '''
                SELECT id, title, filename, category, condition, brand, model,
                       suggested_price, status, created_at, updated_at
                FROM listings
                ORDER BY created_at DESC, id DESC
                '''
            )

            listings = []
            for row in cursor.fetchall():
                listings.append(
                    {
                        "id": row[0],
                        "title": row[1],
                        "filename": row[2],
                        "category": row[3],
                        "condition": row[4],
                        "brand": row[5],
                        "model": row[6],
                        "suggested_price": row[7],
                        "status": row[8],
                        "created_at": row[9],
                        "updated_at": row[10],
                    }
                )

            return listings
    except Exception as e:
        print(f"Error fetching listings: {e}")
        return []


def get_listing(listing_id):
    """Get a specific listing by ID"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute(
                '''
                SELECT id, title, filename, category, condition, brand, model, features,
                       suggested_price, comparable_listings, payload, status, external_listing_id,
                       published_at, publish_error, created_at, updated_at
                FROM listings
                WHERE id = ?
                ''',
                (listing_id,),
            )

            row = cursor.fetchone()

        if not row:
            return None

        try:
            features = json.loads(row[7]) if row[7] else []
        except (json.JSONDecodeError, TypeError):
            features = []

        try:
            comparable_listings = json.loads(row[9]) if row[9] else []
        except (json.JSONDecodeError, TypeError):
            comparable_listings = []

        try:
            payload = json.loads(row[10]) if row[10] else {}
        except (json.JSONDecodeError, TypeError):
            payload = {}

        return {
            "id": row[0],
            "title": row[1],
            "filename": row[2],
            "category": row[3],
            "condition": row[4],
            "brand": row[5],
            "model": row[6],
            "features": features,
            "suggested_price": row[8],
            "comparable_listings": comparable_listings,
            "payload": payload,
            "status": row[11],
            "external_listing_id": row[12],
            "published_at": row[13],
            "publish_error": row[14],
            "created_at": row[15],
            "updated_at": row[16],
        }
    except Exception as e:
        print(f"Error fetching listing {listing_id}: {e}")
        return None


def update_listing_status(listing_id, status):
    """Update listing status (draft, published, archived)"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute(
                '''
                UPDATE listings
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''',
                (status, listing_id),
            )

            updated = cursor.rowcount
            conn.commit()
            return updated > 0
    except Exception as e:
        print(f"Error updating listing status: {e}")
        return False


def delete_listing(listing_id):
    """Delete a listing from database"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM listings WHERE id = ?", (listing_id,))

            deleted = cursor.rowcount
            conn.commit()
            return deleted > 0
    except Exception as e:
        print(f"Error deleting listing: {e}")
        return False


def get_stats():
    """Get database statistics"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM listings")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM listings WHERE status = 'draft'")
            drafts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM listings WHERE status = 'published'")
            published = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM listings WHERE status = 'archived'")
            archived = cursor.fetchone()[0]

        return {"total": total, "drafts": drafts, "published": published, "archived": archived}
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {"total": 0, "drafts": 0, "published": 0, "archived": 0}


def record_publish_result(listing_id, published, external_listing_id=None, error_message=None):
    """Record publish success/failure metadata for a listing."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            if published:
                cursor.execute(
                    '''
                    UPDATE listings
                    SET status = 'published',
                        external_listing_id = ?,
                        published_at = CURRENT_TIMESTAMP,
                        publish_error = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    ''',
                    (external_listing_id, listing_id),
                )
            else:
                cursor.execute(
                    '''
                    UPDATE listings
                    SET publish_error = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    ''',
                    (error_message, listing_id),
                )

            updated = cursor.rowcount
            conn.commit()
            return updated > 0
    except Exception as e:
        print(f"Error recording publish result: {e}")
        return False
