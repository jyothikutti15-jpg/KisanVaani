# KisanVaani — Voice-First AI Farm Advisor

**Every farmer deserves an AI advisor.** KisanVaani lets smallholder farmers get expert agricultural advice through a simple phone call — in their own language. No app. No internet. No smartphone needed.

## The Problem

- 1.3B+ smallholder farmers have zero AI tools
- Every existing solution requires smartphone + internet + English
- 40% post-harvest losses in developing nations due to lack of timely advice

## How It Works

1. **Farmer dials a phone number** (or uses the web demo)
2. **Speaks their question** in Hindi, Telugu, Tamil, Swahili, or English
3. **AI understands and responds** with specific, actionable farming advice in the same language

### Voice Pipeline
```
Farmer speaks → Whisper STT → Claude AI (with farming knowledge) → TTS → Farmer hears answer
```

## Tech Stack

- **Backend**: Python FastAPI + SQLite
- **Voice**: Whisper API (STT) + OpenAI TTS / Google Cloud TTS
- **AI**: Claude (Anthropic) with farming-specific prompt engineering
- **Phone**: Twilio Voice API for real phone calls
- **Frontend**: React + TypeScript + Vite + Tailwind + Recharts

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The app starts in **mock mode** by default (no API keys needed for testing).

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Configuration

Edit `backend/.env` to enable real AI:

```env
MOCK_MODE=false
ANTHROPIC_API_KEY=sk-ant-...    # For Claude farming advisor
OPENAI_API_KEY=sk-...           # For Whisper STT + TTS
TWILIO_ACCOUNT_SID=AC...        # For phone calls (optional)
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
```

## Features

- **Voice Demo**: Browser-based phone simulator with mic recording
- **Text Mode**: Type questions for quick testing
- **5 Languages**: Hindi, Telugu, Tamil, Swahili, English
- **Farming Knowledge**: Crop calendars, government schemes, market prices
- **Admin Dashboard**: Call analytics, language breakdown, timeline charts
- **Call History**: Searchable log of all interactions
- **Twilio Integration**: Real phone call handling via webhooks
- **Mock Mode**: Full pipeline works without API keys for demos

## What Farmers Can Ask

- Pest & disease identification from symptom descriptions
- Crop calendar and planting advice
- Weather-based recommendations
- Current market prices (mandi rates)
- Government scheme eligibility (PM-KISAN, PMFBY, KCC)
- Soil health and fertilizer guidance

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/voice/process` | Web demo: audio → AI response + audio |
| POST | `/api/voice/text` | Text mode: question → AI response + audio |
| GET | `/api/voice/audio/{file}` | Serve generated audio |
| POST | `/api/twilio/incoming` | Handle incoming phone call |
| POST | `/api/twilio/process-speech` | Process spoken question |
| GET | `/api/analytics/overview` | Dashboard stats |
| GET | `/api/analytics/languages` | Language breakdown |
| GET | `/api/analytics/timeline` | Daily call counts |
| GET | `/api/calls` | Call history |
| GET | `/api/languages` | Supported languages |

## License

MIT
