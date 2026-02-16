#!/bin/bash
# Start the eBay Listing Generator web app

echo "🚀 Starting eBay Listing Generator..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "⚠️  No virtual environment found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✓ Virtual environment created and dependencies installed"
fi

# Check if .env exists, if not create from template
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env from template"
fi

# Run the Flask app
echo ""
echo "📱 Web UI running at: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

export PYTHONPATH="${PYTHONPATH}:$(pwd)"
cd /home/j7fargo/VSC-projects-with-git
python -c "from src.app import create_app; app = create_app(); app.run(debug=True, host='0.0.0.0', port=5000)"
