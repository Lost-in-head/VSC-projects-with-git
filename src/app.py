"""
Flask web application for eBay Listing Generator
Provides a user-friendly interface to upload photos and generate listings
"""

import os
import json
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, send_from_directory
from src.config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from src.api.openai_client import describe_image
from src.api.ebay_client import search_ebay, suggest_price, build_listing_payload, publish_listing
from src.database import init_db, save_listing, get_all_listings, get_listing, update_listing_status, delete_listing, get_stats, record_publish_result


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Configuration
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['JSON_SORT_KEYS'] = False
    
    # Initialize database
    init_db()
    
    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    @app.route('/')
    def index():
        """Home page - upload form"""
        stats = get_stats()
        return render_template('index.html', stats=stats)
    
    @app.route('/api/listings', methods=['GET'])
    def get_listings():
        """Get all saved listings"""
        listings = get_all_listings()
        return jsonify(listings), 200
    
    @app.route('/api/listings/<int:listing_id>', methods=['GET'])
    def get_listing_detail(listing_id):
        """Get a specific listing"""
        listing = get_listing(listing_id)
        if not listing:
            return jsonify({'error': 'Listing not found'}), 404
        return jsonify(listing), 200
    
    @app.route('/api/listings/<int:listing_id>/status', methods=['PATCH'])
    def update_status(listing_id):
        """Update listing status"""
        data = request.get_json(silent=True) or {}
        status = data.get('status', 'draft')
        
        if status not in ['draft', 'published', 'archived']:
            return jsonify({'error': 'Invalid status'}), 400
        
        success = update_listing_status(listing_id, status)
        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Listing not found or update failed'}), 404
    
    @app.route('/api/listings/<int:listing_id>', methods=['DELETE'])
    def delete_listing_endpoint(listing_id):
        """Delete a listing"""
        success = delete_listing(listing_id)
        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Listing not found or delete failed'}), 404


    @app.route('/api/listings/<int:listing_id>/publish', methods=['POST'])
    def publish_listing_endpoint(listing_id):
        """Publish a listing and persist publish metadata."""
        listing = get_listing(listing_id)
        if not listing:
            return jsonify({'error': 'Listing not found'}), 404

        if listing.get('status') == 'published':
            return jsonify({'error': 'Listing already published'}), 409

        try:
            publish_result = publish_listing(listing['payload'])
            external_listing_id = publish_result.get('external_listing_id')
            record_publish_result(
                listing_id,
                published=True,
                external_listing_id=external_listing_id,
            )
            updated_listing = get_listing(listing_id)
            return jsonify({
                'success': True,
                'listing_id': listing_id,
                'external_listing_id': external_listing_id,
                'status': updated_listing.get('status') if updated_listing else 'published',
            }), 200
        except Exception as e:
            error_message = str(e)
            record_publish_result(
                listing_id,
                published=False,
                error_message=error_message,
            )
            return jsonify({'error': f'Publish failed: {error_message}'}), 502
    
    @app.route('/api/upload', methods=['POST'])
    def upload_file():
        """Handle photo upload and initiate listing generation"""
        try:
            # Check if file was included in request
            if 'photo' not in request.files:
                return jsonify({'error': 'No photo provided'}), 400
            
            file = request.files['photo']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if not allowed_file(file.filename):
                return jsonify({'error': 'Invalid file type. Use JPG, PNG, or GIF'}), 400
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            timestamp = Path(UPLOAD_FOLDER).glob('*')  # Get next number
            upload_count = len(list(timestamp)) + 1
            filename = f"{upload_count}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the image through the pipeline
            result = process_listing(filepath, filename)
            
            # Clean up uploaded file after processing
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({'error': f'Processing failed: {str(e)}'}), 500
    
    @app.route('/downloads/<filename>')
    def download_file(filename):
        """Download listing as JSON"""
        try:
            return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
        except FileNotFoundError:
            return jsonify({'error': 'File not found'}), 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'File too large. Max 16MB'}), 413
    
    return app




def normalize_analysis_cards(image_analysis):
    """Normalize analysis to a list of card/item analyses."""
    if isinstance(image_analysis, dict) and isinstance(image_analysis.get('cards'), list):
        cards = [card for card in image_analysis['cards'] if isinstance(card, dict)]
        return cards or [image_analysis]
    return [image_analysis]


def build_search_query(analysis):
    """Build search query for general items and trading cards."""
    base = [analysis.get('brand', ''), analysis.get('model', '')]
    category = (analysis.get('category') or '').lower()
    if 'card' in category:
        for key in ('player_name', 'set_name', 'year', 'card_number', 'grade'):
            value = analysis.get(key)
            if value:
                base.append(str(value))
    query = ' '.join(part for part in base if part).strip()
    return query or 'collectible trading card'


def generate_listing_from_analysis(analysis, filename):
    """Generate and persist one listing from one analyzed item/card."""
    search_query = build_search_query(analysis)
    listings = search_ebay(search_query, limit=8)
    suggested_price = suggest_price(listings)

    title = f"{analysis.get('brand', 'Item')} {analysis.get('model', '')}".strip()
    payload = build_listing_payload(
        title=title,
        description=format_description(analysis),
        price=suggested_price,
        condition=analysis.get('condition', 'Unknown')
    )

    listing_id = save_listing(
        title=title,
        filename=filename,
        analysis=analysis,
        comparable_listings=listings,
        suggested_price=suggested_price,
        payload=payload
    )

    return {
        'listing_id': listing_id,
        'analysis': analysis,
        'comparable_listings': listings,
        'suggested_price': suggested_price,
        'payload': payload,
    }

def allowed_file(filename):
    """Check if uploaded file is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_listing(image_path, filename='unknown.jpg'):
    """
    Process image through complete pipeline.
    Supports either one detected item/card or multiple cards in a single image.
    """
    try:
        print(f"📷 Analyzing uploaded image...")
        image_analysis = describe_image(image_path)
        analyses = normalize_analysis_cards(image_analysis)

        print(f"🛒 Searching eBay for similar items...")
        results = [generate_listing_from_analysis(analysis, filename) for analysis in analyses]

        if len(results) == 1:
            result = results[0]
            return {
                'success': True,
                'listing_id': result['listing_id'],
                'analysis': result['analysis'],
                'comparable_listings': result['comparable_listings'],
                'suggested_price': result['suggested_price'],
                'payload': result['payload'],
                'message': '✅ Listing generated and saved successfully!'
            }

        return {
            'success': True,
            'mode': 'multi_card',
            'cards_detected': len(results),
            'card_results': results,
            'message': f'✅ Generated {len(results)} listing drafts from one photo.'
        }

    except Exception as e:
        print(f"❌ Error processing listing: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': '❌ Failed to generate listing'
        }


def format_description(analysis):
    """Format image analysis into eBay listing description"""
    parts = []
    
    if analysis.get('category'):
        parts.append(f"**Category**: {analysis['category']}")
    
    if analysis.get('condition'):
        parts.append(f"**Condition**: {analysis['condition']}")
    
    if analysis.get('features'):
        features_list = analysis['features']
        if isinstance(features_list, list):
            features_text = '\n'.join([f"• {f}" for f in features_list])
        else:
            features_text = features_list
        parts.append(f"**Features**:\n{features_text}")
    
    if analysis.get('brand'):
        parts.append(f"**Brand**: {analysis['brand']}")
    
    if analysis.get('model'):
        parts.append(f"**Model**: {analysis['model']}")
    
    return '\n\n'.join(parts)


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
