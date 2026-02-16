"""
Database models and operations for managing eBay listings
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent / "listings.db"


def init_db():
    """Initialize database with listings table"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()


def save_listing(title, filename, analysis, comparable_listings, suggested_price, payload):
    """Save a generated listing to database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO listings 
            (title, filename, category, condition, brand, model, features, 
             suggested_price, comparable_listings, payload, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title,
            filename,
            analysis.get('category', ''),
            analysis.get('condition', ''),
            analysis.get('brand', ''),
            analysis.get('model', ''),
            json.dumps(analysis.get('features', [])),
            suggested_price,
            json.dumps(comparable_listings),
            json.dumps(payload),
            'draft'
        ))
        
        listing_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return listing_id
    except Exception as e:
        print(f"Error saving listing: {e}")
        return None


def get_all_listings():
    """Get all listings from database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, filename, category, condition, brand, model, 
                   suggested_price, status, created_at, updated_at
            FROM listings
            ORDER BY created_at DESC
        ''')
        
        listings = []
        for row in cursor.fetchall():
            listings.append({
                'id': row[0],
                'title': row[1],
                'filename': row[2],
                'category': row[3],
                'condition': row[4],
                'brand': row[5],
                'model': row[6],
                'suggested_price': row[7],
                'status': row[8],
                'created_at': row[9],
                'updated_at': row[10]
            })
        
        conn.close()
        return listings
    except Exception as e:
        print(f"Error fetching listings: {e}")
        return []


def get_listing(listing_id):
    """Get a specific listing by ID"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, filename, category, condition, brand, model, features,
                   suggested_price, comparable_listings, payload, status, created_at, updated_at
            FROM listings
            WHERE id = ?
        ''', (listing_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'title': row[1],
            'filename': row[2],
            'category': row[3],
            'condition': row[4],
            'brand': row[5],
            'model': row[6],
            'features': json.loads(row[7]) if row[7] else [],
            'suggested_price': row[8],
            'comparable_listings': json.loads(row[9]) if row[9] else [],
            'payload': json.loads(row[10]),
            'status': row[11],
            'created_at': row[12],
            'updated_at': row[13]
        }
    except Exception as e:
        print(f"Error fetching listing {listing_id}: {e}")
        return None


def update_listing_status(listing_id, status):
    """Update listing status (draft, published, archived)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE listings
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, listing_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating listing status: {e}")
        return False


def delete_listing(listing_id):
    """Delete a listing from database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM listings WHERE id = ?', (listing_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting listing: {e}")
        return False


def get_stats():
    """Get database statistics"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM listings')
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM listings WHERE status = 'draft'")
        drafts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM listings WHERE status = 'published'")
        published = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total': total,
            'drafts': drafts,
            'published': published
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {'total': 0, 'drafts': 0, 'published': 0}
