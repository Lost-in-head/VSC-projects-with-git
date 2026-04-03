# eBay Listing Generator App

## What This Does

Upload a photo of an item → AI analyzes it → searches eBay for similar listings → generates a complete eBay listing with title, description, and suggested price.

**Use case**: Quickly create professional eBay listings from photos without manual research.

## Features (in order of building)

1. ✅ Upload/capture photo
2. ✅ Analyze image with OpenAI Vision (extract brand, condition, features)
3. ✅ Search eBay for similar items
4. ✅ Calculate suggested price (median of comparable listings)
5. ✅ Generate listing title & description
6. ✅ Create draft eBay inventory item
7. 🔄 (Optional) Auto-publish to eBay

## Tech Stack

- **Backend**: Python (Flask/FastAPI)
- **Image Analysis**: OpenAI GPT-4o Vision
- **eBay APIs**: Finding API + Sell Inventory API
- **Frontend**: (TBD - web or mobile)

## Current Status: FULLY CONFIGURED ✅

Both OpenAI Vision and eBay APIs are configured and working!

### Getting Started

#### 1. Clone and Setup Environment

```bash
git clone https://github.com/Lost-in-head/VSC-projects-with-git.git
cd VSC-projects-with-git

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```bash
# OpenAI API key (required for image analysis)
OPENAI_API_KEY=sk-your-key-here

# eBay developer credentials (get from https://developer.ebay.com)
EBAY_CLIENT_ID=your-client-id
EBAY_CLIENT_SECRET=your-client-secret

# Set to False to use real APIs
USE_OPENAI_MOCK=False
USE_EBAY_MOCK=False

# Keep True for sandbox testing
EBAY_SANDBOX=True
```

#### 3. Run the App

**Option A: Web UI (Recommended)**

```bash
source venv/bin/activate
bash run_web.sh
# Or manually: python -m flask --app src.app run --debug
```

Open <http://localhost:5000> in your browser.

**Option B: Command Line**

```bash
source venv/bin/activate
python -m src.main
```

### Quick Start - Mock Mode (No API Keys)

Want to try without API keys? Set these in `.env`:

```bash
USE_OPENAI_MOCK=True
USE_EBAY_MOCK=True
```

Then run normally — you'll see realistic demo data.

### Web UI Features

- 📷 Click or drag-drop photo upload
- ✨ Beautiful, modern interface
- 💰 See suggested price instantly
- 🛒 View comparable eBay listings
- 📋 Copy listing JSON to clipboard
- 🚀 Batch processing (upload multiple photos)

## Project Structure

```
.
├── src/
│   ├── main.py                    # Main pipeline (entry point)
│   ├── config.py                  # Load .env configuration
│   ├── app.py                     # Flask web application ⭐
│   ├── models/                    # Data models (future)
│   ├── api/
│   │   ├── openai_client.py       # OpenAI Vision (with mock fallback)
│   │   ├── mock_openai.py         # Realistic mock data for testing
│   │   ├── ebay_client.py         # eBay API (with mock fallback)
│   │   └── mock_ebay.py           # Realistic eBay mock data
│   ├── templates/                 # HTML templates
│   │   └── index.html             # Main web UI
│   ├── static/                    # CSS & JavaScript
│   │   ├── app.js                 # Frontend logic (batch processing)
│   │   └── style.css              # Beautiful gradient UI
│   └── utils/
│       └── helpers.py             # Utility functions
├── requirements.txt
├── .env.example
├── run_web.sh                     # Startup script ⭐
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

## Batch Processing 🚀

**Upload multiple photos at once:**

1. Click or drag-drop multiple photos
2. Review thumbnail grid before processing
3. Click "Generate Listings"
4. See progress bar as each photo is processed
5. View all results in a beautiful grid
6. Copy individual payloads or download all as JSON

**Perfect for:**

- Selling multiple items on eBay
- Bulk listing operations
- Testing multiple products
- Creating listing templates

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

### Phase 3: Real APIs ✅ COMPLETE

- ✅ OpenAI Vision API configured and working
- ✅ eBay Finding API configured and working
- ✅ eBay OAuth authentication working
- ✅ Error handling with mock fallbacks

### Phase 4: Publishing

- Implement eBay Sell API integration
- Auto-publish listings
- Track published listings

### Phase 5: Mobile App 📱 IN PROGRESS

See **[Mobile App](#-mobile-app-react-native--expo)** section below.

---

## 📱 Mobile App (React Native / Expo)

The `mobile/` directory contains a cross-platform mobile app (Android + iOS) built
with [Expo](https://expo.dev) and React Native.  It communicates with the same Flask
backend via its REST API.

### Mobile Features (Phase 1 – MVP)

| Feature | Status |
|---|---|
| Take photo with device camera | ✅ |
| Pick photo from gallery | ✅ |
| Upload photo → AI generates listing | ✅ |
| View single-card result with price | ✅ |
| View multi-card batch result | ✅ |
| Browse all saved listings | ✅ |
| View listing detail | ✅ |
| Publish listing to eBay | ✅ |
| Archive / delete listing | ✅ |
| Configurable backend URL | ✅ |

### Mobile Architecture

```
mobile/
├── App.tsx                          # Entry point
├── app.json                         # Expo config (iOS + Android bundle IDs)
├── package.json                     # npm dependencies
├── tsconfig.json                    # TypeScript config
├── babel.config.js                  # Babel config
└── src/
    ├── api/
    │   └── client.ts                # Typed API client for the Flask backend
    ├── navigation/
    │   └── AppNavigator.tsx         # Bottom-tab + stack navigator
    ├── screens/
    │   ├── HomeScreen.tsx           # Camera / gallery picker + upload
    │   ├── CameraScreen.tsx         # Full-screen camera view
    │   ├── ResultScreen.tsx         # Generated listing result(s)
    │   ├── ListingsScreen.tsx       # Saved-listings list
    │   └── ListingDetailScreen.tsx  # Listing detail + publish / delete
    ├── components/
    │   └── ListingCard.tsx          # Reusable listing card
    └── types/
        └── index.ts                 # Shared TypeScript types
```

### Mobile Prerequisites

- [Node.js 18+](https://nodejs.org/)
- [Expo CLI](https://docs.expo.dev/get-started/installation/): `npm install -g expo-cli`
- For iOS: macOS + Xcode 15+
- For Android: Android Studio + emulator **or** a physical device with [Expo Go](https://expo.dev/client)

### Mobile Quick Start

#### 1. Start the Flask backend

Make sure the backend is running and accessible from your device/emulator:

```bash
# From project root
source venv/bin/activate
bash run_web.sh          # starts on http://0.0.0.0:5000
```

> **Android emulator**: the backend URL is `http://10.0.2.2:5000`  
> **iOS simulator**: use `http://localhost:5000`  
> **Physical device**: use your machine's LAN IP, e.g. `http://192.168.1.42:5000`

#### 2. Configure the backend URL

Edit `mobile/src/api/client.ts` and set `BASE_URL` to the correct address before
building, or call `setBaseUrl(url)` at app startup.

#### 3. Install mobile dependencies

```bash
cd mobile
npm install
```

#### 4. Run the app

```bash
# Interactive Expo menu (scan QR with Expo Go)
npx expo start

# Android emulator
npx expo start --android

# iOS simulator (macOS only)
npx expo start --ios
```

### Building for Production

```bash
# Install EAS CLI
npm install -g eas-cli
eas login

# Configure the project (first time only)
eas build:configure

# Build for Android (.aab / .apk)
eas build --platform android

# Build for iOS (.ipa)
eas build --platform ios
```

### Backend CORS

The Flask backend already has CORS enabled for all `/api/*` routes
(via `flask-cors`), so mobile clients can connect without proxy issues.

## Useful Commands

```bash
# Activate virtual environment (required before running)
source venv/bin/activate

# Run Web UI
python -m flask --app src.app run --debug
# Or: bash run_web.sh

# Run CLI pipeline
python -m src.main

# Run with debug output
DEBUG=True python -m src.main

# Install/update dependencies
pip install -r requirements.txt

# Verify eBay credentials
python -c "from src.api.ebay_client import get_ebay_token; print('OK:', get_ebay_token()[:20])"
```

## Testing the Pipeline

### Test 1: Quick Smoke Test

```bash
source venv/bin/activate
python -m src.main
```

You'll see the full pipeline: image analysis → eBay search → price suggestion → listing JSON.

### Test 2: With Real Image

```bash
# Place any .jpg file at project root named sample_item.jpg
python -m src.main
```

### Test 3: Web UI Upload

```bash
python -m flask --app src.app run --debug
# Open http://localhost:5000
# Upload any photo and see real-time listing generation
```

### Test 4: Verify API Credentials

```bash
# Test eBay
python -c "from src.api.ebay_client import search_ebay; print(search_ebay('laptop', 3))"

# Test OpenAI (requires an image)
python -c "from src.api.openai_client import describe_image; print(describe_image('sample_item.jpg'))"
```

## API Key Setup (When Ready)

### OpenAI

1. Go to <https://platform.openai.com/api-keys>
2. Create a new API key
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

### eBay

1. Register at <https://developer.ebay.com>
2. Create an app
3. Get Client ID and Client Secret
4. Add to `.env`:

   ```bash
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

**Status**: Production-ready! Both OpenAI Vision and eBay APIs configured and working. 🚀
