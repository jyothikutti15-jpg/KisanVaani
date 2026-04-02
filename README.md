# KisanVaani v2.1 — Voice-First AI Farm Advisor

**Every farmer deserves an AI advisor.** KisanVaani lets smallholder farmers get expert agricultural advice through a simple phone call, WhatsApp, or web — in their own language. No app. No internet. No smartphone needed.

> Serving farmers across **India, Kenya, Nigeria, and Ethiopia** in **5 languages**.

---

## The Problem

- **1.3B+ smallholder farmers** have zero access to AI tools
- Every existing solution requires smartphone + internet + English
- **40% post-harvest losses** in developing nations due to lack of timely advice
- Existing agri-tech platforms don't speak the farmer's language

## How It Works

```
Farmer calls / WhatsApp / web demo
        |
Speaks question in their language (Hindi, Telugu, Tamil, Swahili, English)
        |
Claude AI understands context (crop, soil, location, season, history)
        |
Returns specific, actionable advice in the same language
        |
Farmer hears the answer read aloud
```

---

## Features

### Core Voice Pipeline
- **Voice Demo** — Browser-based phone simulator with mic recording
- **Phone Calls** — Real IVR via Twilio (works on any basic phone)
- **WhatsApp Integration** — Text, photos, and voice via WhatsApp
- **5 Languages** — Hindi, Telugu, Tamil, Swahili, English
- **Text Mode** — Type questions directly for testing
- **Multi-turn Conversations** — AI remembers context across turns

### AI Farming Intelligence
- **Pest & Disease Diagnosis** — From text description or photo upload
- **Photo Diagnosis** — Upload crop images for Claude Vision analysis
- **Crop Calendar** — Region and season-specific planting advice
- **Weather Forecasts** — Live 7-day forecast from Open-Meteo (free API)
- **Soil Health** — Fertilizer recommendations based on soil type
- **Yield Estimation** — Predict harvest based on crop, soil, irrigation

### Farmer Memory System
- **Persistent Profiles** — Name, location, crops, land size, soil, irrigation
- **Session History** — Remembers past conversations (SQLite-backed)
- **Personalized Advice** — "Welcome back Ramesh! How is your tomato doing?"
- **Auto-Memory Update** — AI updates farmer profile after each interaction

### Smart Financial Tools
- **Expense Tracking** — AI auto-detects expenses from conversation ("I spent 2000 on urea")
- **Expense Summaries** — By category (fertilizer, seeds, pesticide, labor) and by crop
- **Loan Eligibility** — KCC, PM-KISAN, PMFBY (India), AFC (Kenya), Anchor Borrowers (Nigeria)
- **AI Price Predictor** — Predicts mandi prices using trend + seasonal analysis with HOLD/SELL recommendations

### Satellite Crop Monitoring
- **NDVI Analysis** — Vegetation health scoring from satellite data
- **Early Stress Detection** — Detects crop stress before the farmer notices
- **Regional Comparison** — Compare your field's health vs regional average
- **Actionable Alerts** — Specific recommendations based on NDVI score

### Proactive Outbound System
- **Smart Crop Reminders** — Irrigation, fertilizer, pest check schedules based on crop diary
- **Weather Alerts** — Auto-notify farmers when severe weather affects their region/crops
- **Price Alerts** — Notify when prices spike for their crops
- **Scheme Deadlines** — PM-KISAN registration, insurance deadlines
- **Multi-channel Delivery** — Via WhatsApp or voice call

### Expert Callback System
- **Human Escalation** — When AI confidence is low, routes to human agronomist
- **Priority Queue** — Urgent issues (livestock, disease) get priority 1
- **Expert Dashboard** — Agronomists can view, assign, and resolve tickets
- **48-hour SLA** — Farmers receive expert callback within 48 hours

### Farmer Community Network
- **Peer Q&A** — Anonymized questions and answers shared by region
- **Upvoting** — Farmers mark helpful answers
- **Trending Topics** — See what problems are most reported in your area
- **Community Intelligence** — Aggregated insights from farmer queries

### Marketplace
- **Buy/Sell Listings** — Farmers list produce directly (no middleman)
- **Crop Search** — Browse by crop, region, listing type
- **30-day Expiry** — Auto-cleanup of stale listings
- **Direct Contact** — Buyers connect with farmers directly

### Analytics Dashboard
- **Overview Stats** — Total calls, sessions, languages, daily volume
- **Language Breakdown** — Which languages farmers use most
- **Call Timeline** — 30-day bar chart of call volume
- **Call History** — Searchable, filterable log of all interactions
- **Farmer Reports** — Comprehensive profile + expenses + diary + reminders

### Additional Features
- **KVK Locator** — Find nearest Krishi Vigyan Kendra / extension center
- **Pest Gallery** — Database of common pests with treatments and dosages
- **Crop Diary** — Log planting, irrigation, fertilizing, harvesting activities
- **Auto-generated Reminders** — Based on crop diary entries
- **Government Schemes** — Country-specific scheme info and application steps
- **4-Country Support** — India, Kenya, Nigeria, Ethiopia with localized content

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python FastAPI + SQLAlchemy + SQLite |
| **AI** | Claude (Anthropic) — claude-sonnet-4-6 with farming prompt |
| **Voice** | Web Speech API (STT) + Google Translate TTS (free) |
| **Phone** | Twilio Voice API + WhatsApp Business API |
| **Weather** | Open-Meteo API (free, no key needed) |
| **Frontend** | React 18 + TypeScript + Vite + Tailwind CSS + Recharts |
| **Deployment** | Docker + docker-compose |

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
docker-compose up --build
```

Open http://localhost:8000

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

The app starts in **mock mode** by default — no API keys needed for testing.

---

## Configuration

Edit `backend/.env`:

```env
# Required for real AI (set MOCK_MODE=false)
MOCK_MODE=true
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Phone calls and WhatsApp
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# Optional: CORS origins
CORS_ORIGINS=["http://localhost:5173","http://localhost:8000"]

# Optional: Rate limiting
RATE_LIMIT=30/minute
MAX_INPUT_LENGTH=2000
AUDIO_CACHE_TTL_HOURS=24
```

---

## API Reference

### Voice & AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/voice/text` | Text question -> AI response + audio |
| POST | `/api/voice/photo` | Photo upload -> crop disease diagnosis |
| GET | `/api/voice/audio/{file}` | Serve generated audio files |

### Phone & WhatsApp

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/twilio/incoming` | Handle incoming phone call (IVR) |
| POST | `/api/twilio/process-speech` | Process spoken question from call |
| POST | `/api/whatsapp/webhook` | Handle incoming WhatsApp messages |
| POST | `/api/whatsapp/send` | Send outbound WhatsApp message |
| GET | `/api/whatsapp/conversations/{farmer_id}` | WhatsApp conversation history |

### Price Prediction

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/prices/predict/{crop}?days=7` | Predict future mandi price |
| GET | `/api/prices/trends/{crop}?days=30` | Historical price trend data |

### Satellite Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/satellite/analyze` | NDVI crop health analysis |
| GET | `/api/satellite/history/{farmer_id}` | Satellite monitoring history |
| GET | `/api/satellite/regional/{location}` | Regional crop health overview |

### Expert Callbacks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/expert/request` | Request human expert callback |
| GET | `/api/expert/queue` | View expert callback queue |
| POST | `/api/expert/{ticket_id}/resolve` | Expert resolves a ticket |
| GET | `/api/expert/stats` | Expert system statistics |

### Farmer Network & Community

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/community/share` | Share anonymized Q&A |
| GET | `/api/community/questions` | Browse community Q&A |
| POST | `/api/community/questions/{id}/helpful` | Upvote helpful answer |
| GET | `/api/community/trending` | Trending farming topics |
| GET | `/api/community` | Community insights (aggregated) |

### Marketplace

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/marketplace/listings` | Create buy/sell listing |
| GET | `/api/marketplace/listings` | Browse marketplace |
| GET | `/api/marketplace/stats` | Marketplace statistics |

### Proactive Calls

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/proactive/generate` | Generate scheduled reminders |
| POST | `/api/proactive/deliver` | Deliver pending calls |
| GET | `/api/proactive/queue` | View call queue |
| GET | `/api/proactive/stats` | Proactive call statistics |

### Farmer Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/onboard` | Quick farmer onboarding |
| POST | `/api/farmers` | Create farmer profile |
| GET | `/api/farmers` | List farmers |
| GET | `/api/farmers/{id}` | Get farmer details |
| PUT | `/api/farmers/{id}` | Update farmer profile |
| GET | `/api/report/{farmer_id}` | Comprehensive farmer report |

### Expenses

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/expenses` | Log expense manually |
| GET | `/api/expenses/{farmer_id}` | Get farmer's expenses |
| GET | `/api/expenses/{farmer_id}/summary` | Expense summary by category |

### Features

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/weather/{location}` | Weather forecast (3-7 days) |
| GET | `/api/kvk/{country}/{region}` | Find extension centers |
| POST | `/api/yield/predict` | Estimate crop yield |
| GET | `/api/loans/{country}` | Loan eligibility by country |
| GET | `/api/pests` | List all pests |
| GET | `/api/pests/{name}` | Pest details with treatments |
| POST | `/api/diary` | Add crop diary entry |
| GET | `/api/diary/{farmer_id}` | Get diary entries |
| GET | `/api/reminders/{farmer_id}` | Pending and upcoming reminders |

### Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/alerts` | Create alert |
| GET | `/api/alerts` | List alerts (filter by country) |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/overview` | Dashboard stats |
| GET | `/api/analytics/languages` | Language breakdown |
| GET | `/api/analytics/timeline` | Daily call counts (30 days) |
| GET | `/api/calls` | Call history with pagination |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check (DB, AI, Twilio status) |
| GET | `/api/languages` | Supported languages |
| GET | `/api/countries` | Country data |

---

## Supported Languages & Countries

| Language | Code | Script |
|----------|------|--------|
| Hindi | hi | हिन्दी |
| Telugu | te | తెలుగు |
| Tamil | ta | தமிழ் |
| Swahili | sw | Kiswahili |
| English | en | English |

| Country | Code | Key Schemes |
|---------|------|-------------|
| India | IN | KCC, PM-KISAN, PMFBY, Soil Health Card |
| Kenya | KE | NARIGP, e-Voucher, AFC loans |
| Nigeria | NG | Anchor Borrowers, Growth Enhancement |
| Ethiopia | ET | PSNP, Agricultural Growth Program |

---

## Testing

```bash
cd backend
python -m pytest tests/ -v
```

**80 tests** covering all features:
- Voice pipeline (5 languages, multi-turn, validation)
- Security (rate limiting, path traversal, input sanitization)
- Price prediction (trends, recommendations, unknown crops)
- Satellite NDVI (coordinates, location name, history)
- Expert callbacks (request, queue, resolve, stats)
- Farmer network (share, browse, upvote, trending)
- Marketplace (buy/sell listings, browse, stats)
- Proactive calls (generate, deliver, queue)
- WhatsApp (webhook, conversations, send)
- All existing features (weather, pests, loans, KVK, yield, diary)

---

## Project Structure

```
KisanVaani/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app, middleware, lifespan
│   │   ├── config.py                  # Settings, languages, constants
│   │   ├── database.py                # SQLAlchemy setup
│   │   ├── models/
│   │   │   ├── call.py                # CallLog
│   │   │   ├── farmer.py             # FarmerProfile, FarmerExpense
│   │   │   ├── crop_diary.py         # CropDiaryEntry, CropReminder
│   │   │   ├── alert.py              # Alert, CommunityInsight
│   │   │   ├── session.py            # ConversationTurn (persistent sessions)
│   │   │   ├── whatsapp.py           # WhatsAppMessage
│   │   │   ├── proactive.py          # ScheduledCall, PriceHistory
│   │   │   └── marketplace.py        # ExpertCallback, FarmerQuestion, MarketListing, SatelliteReport
│   │   ├── routers/
│   │   │   ├── web_voice.py          # Voice pipeline endpoints
│   │   │   ├── twilio_voice.py       # Phone call handling
│   │   │   ├── whatsapp.py           # WhatsApp integration
│   │   │   ├── analytics.py          # Dashboard & call history
│   │   │   ├── farmers.py            # Farmer CRUD
│   │   │   ├── alerts.py             # Alerts & community insights
│   │   │   ├── expenses.py           # Expense tracking
│   │   │   ├── features.py           # Weather, KVK, yield, loans, pests, diary
│   │   │   ├── advanced.py           # Price prediction, satellite, expert, marketplace, network
│   │   │   └── proactive.py          # Outbound call scheduling
│   │   ├── services/
│   │   │   ├── llm_service.py        # Claude AI with retry logic
│   │   │   ├── tts_service.py        # Google Translate TTS with retry
│   │   │   ├── stt_service.py        # Speech-to-text (browser-native)
│   │   │   ├── voice_pipeline.py     # Text/audio processing pipeline
│   │   │   ├── farming_knowledge.py  # Context builder from data files
│   │   │   ├── weather_service.py    # Open-Meteo weather API
│   │   │   ├── extra_services.py     # KVK, yield, loans, diary, pests
│   │   │   ├── price_predictor.py    # AI mandi price prediction
│   │   │   ├── satellite_service.py  # NDVI crop health monitoring
│   │   │   └── proactive_service.py  # Smart reminder generation
│   │   └── data/                     # JSON knowledge bases
│   ├── tests/
│   │   ├── test_api.py               # Core feature tests (45)
│   │   └── test_advanced.py          # Advanced feature tests (35)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx                   # Routes with ErrorBoundary
│   │   ├── pages/                    # Landing, VoiceDemo, Dashboard, etc.
│   │   ├── components/               # Navbar, ErrorBoundary
│   │   └── api/                      # Axios client
│   ├── public/
│   │   ├── manifest.json             # PWA manifest
│   │   └── sw.js                     # Service worker
│   └── index.html                    # PWA meta tags
├── Dockerfile                        # Multi-stage build
├── docker-compose.yml                # One-command deployment
└── .env.example                      # Configuration template
```

---

## What Makes KisanVaani Unique

| Feature | KisanVaani | Most Competitors |
|---------|-----------|-----------------|
| Works on basic phone (no internet) | Yes (Twilio IVR) | No (require app/smartphone) |
| Farmer memory across sessions | Yes (persistent profiles) | No (each query independent) |
| Voice-based expense tracking | Yes (AI auto-detects) | No (manual entry) |
| Photo diagnosis via WhatsApp | Yes (Claude Vision) | Limited |
| AI price predictions | Yes (trend + seasonal) | Static prices only |
| Satellite crop monitoring | Yes (NDVI analysis) | Enterprise-only |
| Human expert fallback | Yes (48hr callback SLA) | No |
| Peer farmer network | Yes (anonymized Q&A) | Separate apps |
| Multi-country from day 1 | Yes (4 countries, 5 languages) | Usually single-country |
| Proactive outbound calls | Yes (smart reminders) | Rare |
| Farmer marketplace | Yes (buy/sell listings) | Separate platforms |

---

## License

MIT
