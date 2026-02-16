# eBay Listing Generator App

## What This Does
Upload a photo of an item → AI analyzes it → searches eBay for similar listings → generates a complete eBay listing with title, description, and suggested price.

**Use case**: Quickly create professional eBay listings from photos without manual research.

## Features (in order of building)
1. ✅ Upload/capture photo
2. 🔄 Analyze image with OpenAI Vision (extract brand, condition, features)
3. 🔍 Search eBay for similar items
4. 💰 Calculate suggested price (median of comparable listings)
5. 📝 Generate listing title & description
6. 📦 Create draft eBay inventory item
7. ✨ (Optional) Auto-publish to eBay

## Tech Stack
- **Backend**: Python (Flask/FastAPI)
- **Image Analysis**: OpenAI GPT-4o Vision
- **eBay APIs**: Finding API + Sell Inventory API
- **Frontend**: (TBD - web or mobile)

## Current Status: MOCK MODE ✨
You can run the app RIGHT NOW without API keys! We use realistic mock data for testing.

### Getting Started

#### Quick Start - Web UI (Recommended!)
```bash
bash run_web.sh
# Open http://localhost:5000 in your browser
# Upload a photo → See instant listing!
```

**Features:**
- 📷 Click or drag-drop photo upload
- ✨ Beautiful, modern interface
- 💰 See suggested price instantly
- 🛒 View comparable eBay listings
- 📋 Copy listing JSON to clipboard

#### Quick Start - Command Line (No Setup Needed!)
```bash
cd /path/to/VSC-projects-with-git
pip install -r requirements.txt
python src/main.py
```

That's it! You'll see realistic demo data flowing through the pipeline.

#### With Real API Keys (When Ready)
1. Copy `.env.example` to `.env`
2. Add your OpenAI API key
3. Add your eBay credentials
4. Set `USE_OPENAI_MOCK=False` and `USE_EBAY_MOCK=False` in `.env`
5. Run: `python src/main.py`

## Project Structure
```
.
├── src/
│   ├── main.py                    # Main pipeline (entry point)
│   ├── config.py                  # Load .env configuration
│   ├── models/                    # Data models (future)
│   ├── api/
│   │   ├── openai_client.py       # OpenAI Vision (with mock fallback)
│   │   ├── mock_openai.py         # Realistic mock data for testing
│   │   ├── ebay_client.py         # eBay API (with mock fallback)
│   │   └── mock_ebay.py           # Realistic eBay mock data
│   └── utils/
│       └── helpers.py             # Utility functions
├── requirements.txt
├── .env.example
└── README.md
```

## How Mock Mode Works

**What's happening under the hood:**
- `USE_OPENAI_MOCK=True` → Returns realistic demo item data instead of calling OpenAI
- `USE_EBAY_MOCK=True` → Returns realistic comparable listings instead of calling eBay API
- **Result**: Full end-to-end pipeline works for testing, learning, and demo purposes!

### Mock Data Examples
- MacBook Air M2 2023
- Sony WH-1000XM4 Headphones
- Canon EOS R6 Camera
- Patagonia Down Jacket
- Dyson V15 Vacuum

## Next Steps - Development Roadmap

### Phase 1: Core Pipeline ✅ COMPLETE
- ✅ Mock image analysis
- ✅ Mock eBay search
- ✅ Price suggestion algorithm
- ✅ Listing payload generation

### Phase 2: Web Interface ✅ COMPLETE
- ✅ Build Flask web UI for photo upload
- ✅ Real-time preview of generated listings
- ✅ Beautiful, responsive design
- ✅ Copy-to-clipboard for listing JSON

### Phase 3: Real APIs (Next)
- Add your OpenAI key → Enable real image analysis
- Add eBay credentials → Enable real product search
- Implement error handling

### Phase 4: Publishing
- Implement eBay Sell API integration
- Auto-publish listings
- Track published listings

## Useful Commands

### Run the Web UI (Recommended!)
```bash
bash run_web.sh
```
Then open http://localhost:5000 in your browser! 🎉

### Run with mock data (command line)
```bash
python src/main.py
```

### Run with debug output
```bash
DEBUG=True python src/main.py
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Set up environment
```bash
cp .env.example .env
# Edit .env with your keys (when you have them)
```

## Testing the Pipeline

**Test 1: No Setup Required**
- Run `python src/main.py` 
- You'll see realistic mock data flowing through
- The pipeline outputs a complete eBay listing JSON

**Test 2: With Real Image**
- Place any `.jpg` file at project root and name it `sample_item.jpg`
- Run `python src/main.py`
- (In mock mode, it still uses demo analysis)

**Test 3: With OpenAI Key**
- Add `OPENAI_API_KEY=sk-...` to `.env`
- Set `USE_OPENAI_MOCK=False` in `.env`
- Run `python src/main.py`
- Now you'll see REAL image analysis!

## API Key Setup (When Ready)

### OpenAI
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

### eBay 
1. Register at https://developer.ebay.com
2. Create an app
3. Get Client ID and Client Secret
4. Add to `.env`:
   ```
   EBAY_CLIENT_ID=your-id
   EBAY_CLIENT_SECRET=your-secret
   ```

## Commits & Progress Tracking

Each development session, commit your work:
```bash
git add .
git commit -m "Add feature description"
git log --oneline  # See all your progress
```

Track in README's "Current Status" section!

## Troubleshooting

**Q: "ImportError: No module named 'requests'"**
A: Run `pip install -r requirements.txt`

**Q: "FileNotFoundError: sample_item.jpg"**
A: This is fine! In mock mode, we use demo data anyway.

**Q: Real API calls not working**
A: Check `.env` - make sure `USE_OPENAI_MOCK` and `USE_EBAY_MOCK` are set to `False` and your keys are valid.

---

**Status**: Ready for development! Mock mode works, real APIs coming soon. 🚀 
