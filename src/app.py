"""
Flask web application for eBay Listing Generator
Provides a user-friendly interface to upload photos and generate listings
"""

import importlib
import logging
import os
import tempfile
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from src.config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH, HIGH_VALUE_THRESHOLD
from src.logging_config import configure_logging
from src.validators import ImageValidator
from src.api.openai_client import describe_image
from src.api.ebay_client import search_ebay, suggest_price, build_listing_payload, publish_listing
from src.database import init_db, save_listing, get_all_listings, get_listing, update_listing_status, delete_listing, get_stats, record_publish_result
import src.settings_store as settings_store

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure Flask application"""
    configure_logging()

    app = Flask(__name__, template_folder='templates', static_folder='static')

    # Enable CORS for all API routes (required for mobile/desktop WebView clients)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Configuration
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
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
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo provided'}), 400

        file = request.files['photo']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        original_filename = secure_filename(file.filename)

        # Validate filename. Use actual file size when content-length is available;
        # pass 1 as a placeholder when unknown so the size check is skipped here
        # (the web server enforces MAX_CONTENT_LENGTH independently).
        file_size = request.content_length if request.content_length is not None else 1
        is_valid, err_msg = ImageValidator.validate_upload(original_filename, file_size)
        if not is_valid:
            return jsonify({'error': err_msg}), 400

        # Save to a guaranteed-unique temp file; always cleaned up even on crash
        suffix = os.path.splitext(original_filename)[1] or '.jpg'
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=suffix,
                dir=app.config['UPLOAD_FOLDER'],
                delete=False,
            ) as tmp:
                tmp_path = tmp.name
                file.save(tmp_path)

            result = process_listing(tmp_path, original_filename)

        except Exception:
            logger.exception("Upload pipeline failed for %s", original_filename)
            return jsonify({'error': 'Processing failed. Please try again.'}), 500
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

        status_code = 200 if result.get('success') else 500
        return jsonify(result), status_code
    
    @app.route('/downloads/<filename>')
    def download_file(filename):
        """Download listing as JSON"""
        try:
            return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
        except FileNotFoundError:
            return jsonify({'error': 'File not found'}), 404
    
    @app.route('/api/health')
    def health():
        """Health check endpoint for desktop/mobile connectivity checks"""
        return jsonify({'status': 'ok', 'version': '1.0.0'}), 200

    # ── Settings routes ───────────────────────────────────────────────────────

    @app.route('/settings')
    def settings_page():
        """Settings UI — enter API keys and toggle mock/sandbox mode"""
        return render_template('settings.html')

    @app.route('/api/settings', methods=['GET'])
    def get_settings():
        """Return current settings state (secrets are masked)."""
        import src.config as cfg
        stored = settings_store.load_all()

        def _mask(key):
            val = stored.get(key, '')
            if not val:
                return ''
            # Show first 4 chars then asterisks, e.g. sk-p***
            visible = val[:4]
            return visible + '*' * max(4, len(val) - 4)

        return jsonify({
            'openai_api_key_set': bool(stored.get('OPENAI_API_KEY')),
            'openai_api_key_preview': _mask('OPENAI_API_KEY'),
            'ebay_client_id_set': bool(stored.get('EBAY_CLIENT_ID')),
            'ebay_client_id_preview': _mask('EBAY_CLIENT_ID'),
            'ebay_client_secret_set': bool(stored.get('EBAY_CLIENT_SECRET')),
            'use_openai_mock': os.environ.get('USE_OPENAI_MOCK', str(cfg.USE_OPENAI_MOCK)).lower() == 'true',
            'use_ebay_mock': os.environ.get('USE_EBAY_MOCK', str(cfg.USE_EBAY_MOCK)).lower() == 'true',
            'ebay_sandbox': os.environ.get('EBAY_SANDBOX', str(cfg.EBAY_SANDBOX)).lower() == 'true',
        }), 200

    @app.route('/api/settings', methods=['POST'])
    def save_settings():
        """
        Save API credentials and toggle flags.
        Reloads config and API client modules so changes take effect immediately
        without restarting the server.
        """
        data = request.get_json(silent=True) or {}

        # Build a settings dict from the submitted values
        to_save = {}
        for key in ('OPENAI_API_KEY', 'EBAY_CLIENT_ID', 'EBAY_CLIENT_SECRET'):
            if key in data:
                to_save[key] = data[key]

        for key in ('USE_OPENAI_MOCK', 'USE_EBAY_MOCK', 'EBAY_SANDBOX'):
            if key in data:
                to_save[key] = 'True' if data[key] else 'False'

        settings_store.save_all(to_save)

        # Apply to os.environ so that reloaded modules pick up the new values
        for key, value in to_save.items():
            if value:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)

        # Reload config and API client modules to apply changes live
        import src.config as config_mod
        import src.api.openai_client as openai_mod
        import src.api.ebay_client as ebay_mod
        importlib.reload(config_mod)
        importlib.reload(openai_mod)
        importlib.reload(ebay_mod)
        logger.info("Settings saved and modules reloaded")

        return jsonify({'success': True}), 200

    @app.route('/api/settings/test-openai', methods=['POST'])
    def test_openai():
        """Quick connectivity test against the OpenAI API."""
        import src.config as cfg
        if cfg.USE_OPENAI_MOCK or not cfg.OPENAI_API_KEY:
            return jsonify({
                'success': True,
                'mode': 'mock',
                'message': 'Mock mode active — no API call made',
            }), 200
        try:
            import requests as req
            resp = req.get(
                'https://api.openai.com/v1/models',
                headers={'Authorization': f'Bearer {cfg.OPENAI_API_KEY}'},
                timeout=8,
            )
            if resp.status_code == 200:
                return jsonify({'success': True, 'mode': 'live', 'message': 'OpenAI connection successful ✅'}), 200
            return jsonify({'success': False, 'message': f'OpenAI returned HTTP {resp.status_code}'}), 200
        except Exception as exc:
            return jsonify({'success': False, 'message': f'Connection error: {exc}'}), 200

    @app.route('/api/settings/test-ebay', methods=['POST'])
    def test_ebay():
        """Quick connectivity test against the eBay API."""
        import src.config as cfg
        if cfg.USE_EBAY_MOCK or not cfg.EBAY_CLIENT_ID or not cfg.EBAY_CLIENT_SECRET:
            return jsonify({
                'success': True,
                'mode': 'mock',
                'message': 'Mock mode active — no API call made',
            }), 200
        try:
            from src.api.ebay_client import get_ebay_token
            get_ebay_token()
            mode = 'sandbox' if cfg.EBAY_SANDBOX else 'production'
            return jsonify({'success': True, 'mode': mode, 'message': f'eBay connection successful ✅ ({mode})'}), 200
        except Exception as exc:
            return jsonify({'success': False, 'message': f'eBay auth failed: {exc}'}), 200

    # ── Error handlers ────────────────────────────────────────────────────────

    @app.errorhandler(413)
    def request_entity_too_large(error):
        from src.config import MAX_UPLOAD_SIZE_MB
        return jsonify({'error': f'File too large. Max {MAX_UPLOAD_SIZE_MB}MB'}), 413
    
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


def _build_listing_title(analysis):
    """
    Build an optimised eBay listing title from image analysis.

    For trading-card categories the player name is the most important
    search keyword, so it is prepended when it is not already present
    in the model field.  For all other categories the legacy
    "{brand} {model}" format is used.
    """
    brand = analysis.get('brand', 'Item')
    model = analysis.get('model', '')
    category = analysis.get('category', '').lower()

    if 'card' in category:
        player_name = analysis.get('player_name', '')
        # Only prepend player_name when it is absent from the model string
        if player_name and player_name.lower() not in model.lower():
            return f"{player_name} {brand} {model}".strip()

    return f"{brand} {model}".strip()


def generate_listing_from_analysis(analysis, filename):
    """Generate and persist one listing from one analyzed item/card."""
    search_query = build_search_query(analysis)
    listings = search_ebay(search_query, limit=8)
    suggested_price = suggest_price(listings)

    if suggested_price is None:
        suggested_price = 5.00
        price_warning = True
    else:
        price_warning = False

    title = _build_listing_title(analysis)
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

    if listing_id is None:
        raise RuntimeError("Failed to save listing to database")

    return {
        'listing_id': listing_id,
        'analysis': analysis,
        'comparable_listings': listings,
        'suggested_price': suggested_price,
        'price_warning': price_warning,
        'is_high_value': suggested_price >= HIGH_VALUE_THRESHOLD,
        'payload': payload,
    }

def allowed_file(filename):
    """Check if uploaded file is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_listing(image_path, filename='unknown.jpg'):
    """
    Process image through complete pipeline.

    Always returns a normalised response::

        {
            'success': bool,
            'listings': [ListingResult, ...],  # always a list
            'count': int,
            'high_value_threshold': float,
            'message': str,
        }

    On failure ``listings`` is ``[]`` and an ``'error'`` key is present.
    """
    try:
        logger.info("Analyzing uploaded image...")
        image_analysis = describe_image(image_path)
        analyses = normalize_analysis_cards(image_analysis)

        if not analyses:
            return {
                'success': False,
                'listings': [],
                'count': 0,
                'high_value_threshold': HIGH_VALUE_THRESHOLD,
                'error': 'No items detected in image',
                'message': '❌ Could not identify any items in the photo',
            }

        logger.info("Searching eBay for similar items...")
        results = [generate_listing_from_analysis(analysis, filename) for analysis in analyses]
        count = len(results)
        msg = (
            f"✅ Generated {count} listing draft{'s' if count != 1 else ''} from one photo."
        )
        return {
            'success': True,
            'listings': results,
            'count': count,
            'high_value_threshold': HIGH_VALUE_THRESHOLD,
            'message': msg,
        }

    except Exception as e:
        logger.exception("Error processing listing for %s", filename)
        return {
            'success': False,
            'listings': [],
            'count': 0,
            'high_value_threshold': HIGH_VALUE_THRESHOLD,
            'error': 'Failed to generate listing',
            'message': '❌ Failed to generate listing',
        }


def format_description(analysis):
    """Format image analysis into eBay listing description"""
    parts = []
    
    if analysis.get('category'):
        parts.append(f"**Category**: {analysis['category']}")
    
    if analysis.get('condition'):
        parts.append(f"**Condition**: {analysis['condition']}")

    # Trading-card specific fields
    card_fields = [
        ('player_name', 'Player'),
        ('set_name', 'Set'),
        ('year', 'Year'),
        ('card_number', 'Card Number'),
        ('grade', 'Grade'),
    ]
    for key, label in card_fields:
        if analysis.get(key):
            parts.append(f"**{label}**: {analysis[key]}")

    if analysis.get('grading_notes'):
        notes = analysis['grading_notes']
        if isinstance(notes, list):
            notes_text = '\n'.join([f"• {n}" for n in notes])
        else:
            notes_text = str(notes)
        parts.append(f"**Grading Notes**:\n{notes_text}")

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
    from src.config import DEBUG
    app = create_app()
    app.run(debug=DEBUG, host='127.0.0.1', port=5000)
