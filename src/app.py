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
from src.api.ebay_client import search_ebay, suggest_price, build_listing_payload
from src.database import init_db, save_listing, get_all_listings, get_listing, update_listing_status, delete_listing, get_stats


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
        data = request.get_json()
        status = data.get('status', 'draft')
        
        if status not in ['draft', 'published', 'archived']:
            return jsonify({'error': 'Invalid status'}), 400
        
        success = update_listing_status(listing_id, status)
        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Update failed'}), 500
    
    @app.route('/api/listings/<int:listing_id>', methods=['DELETE'])
    def delete_listing_endpoint(listing_id):
        """Delete a listing"""
        success = delete_listing(listing_id)
        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Delete failed'}), 500
    
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


def allowed_file(filename):
    """Check if uploaded file is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_listing(image_path, filename='unknown.jpg'):
    """
    Process image through complete pipeline
    Returns dict with all listing information and saves to database
    """
    try:
        # Step 1: Analyze image
        print(f"📷 Analyzing uploaded image...")
        image_analysis = describe_image(image_path)
        
        # Step 2: Search eBay for similar items
        print(f"🛒 Searching eBay for similar items...")
        search_query = f"{image_analysis.get('brand', '')} {image_analysis.get('model', '')}"
        listings = search_ebay(search_query, limit=5)
        
        # Step 3: Calculate suggested price
        print(f"💰 Calculating suggested price...")
        suggested_price = suggest_price(listings)
        
        # Step 4: Build listing payload
        print(f"📦 Building eBay listing...")
        title = image_analysis.get('brand', 'Item')
        payload = build_listing_payload(
            title=title,
            description=format_description(image_analysis),
            price=suggested_price,
            condition=image_analysis.get('condition', 'Unknown')
        )
        
        # Step 5: Save to database
        listing_id = save_listing(
            title=title,
            filename=filename,
            analysis=image_analysis,
            comparable_listings=listings,
            suggested_price=suggested_price,
            payload=payload
        )
        
        return {
            'success': True,
            'listing_id': listing_id,
            'analysis': image_analysis,
            'comparable_listings': listings,
            'suggested_price': suggested_price,
            'payload': payload,
            'message': '✅ Listing generated and saved successfully!'
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
