# KisanVaani — Deployment Guide

## Quick Start (Docker)

### Prerequisites
- Docker and Docker Compose installed

### Steps

```bash
# Clone the repository
git clone https://github.com/jyothikutti15-jpg/KisanVaani.git
cd KisanVaani

# Copy and configure environment
cp .env.example backend/.env
# Edit backend/.env with your API keys

# Build and run
docker-compose up --build
```

The app will be available at **http://localhost:8000**

### Docker Environment Variables

```yaml
environment:
  - MOCK_MODE=true                    # Set false for real AI
  - ANTHROPIC_API_KEY=sk-ant-...      # Required for real AI
  - TWILIO_ACCOUNT_SID=AC...          # Optional: phone/WhatsApp
  - TWILIO_AUTH_TOKEN=...
  - TWILIO_PHONE_NUMBER=+1...
  - CORS_ORIGINS=["http://localhost:8000"]
```

---

## Manual Deployment

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
source venv/Scripts/activate    # Windows Git Bash

# Install dependencies
pip install -r requirements.txt

# Configure
cp ../.env.example .env
# Edit .env with your settings

# Run
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

npm install
npm run build    # Production build -> dist/

# Serve with any static file server
npx serve dist -l 5173
```

### Frontend with Vite Dev Server (Development)

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173 with hot reload
```

The Vite dev server proxies `/api/*` requests to the backend at `localhost:8000`.

---

## Production Deployment

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MOCK_MODE` | No | `true` | Set `false` to use real Claude AI |
| `ANTHROPIC_API_KEY` | Yes (if not mock) | `""` | Anthropic API key for Claude |
| `TWILIO_ACCOUNT_SID` | No | `""` | Twilio account SID for phone/WhatsApp |
| `TWILIO_AUTH_TOKEN` | No | `""` | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | No | `""` | Twilio phone number |
| `DATABASE_URL` | No | `sqlite:///./kisanvaani.db` | Database connection string |
| `CORS_ORIGINS` | No | `["http://localhost:5173"]` | Allowed CORS origins (JSON array) |
| `RATE_LIMIT` | No | `30/minute` | API rate limit |
| `MAX_INPUT_LENGTH` | No | `2000` | Max text input characters |
| `AUDIO_CACHE_TTL_HOURS` | No | `24` | Audio file cleanup interval |

### Setting Up Twilio

#### Phone Calls
1. Create a Twilio account at https://twilio.com
2. Buy a phone number with Voice capability
3. Set the Voice webhook to `https://your-domain/api/twilio/incoming`
4. Add credentials to `.env`

#### WhatsApp
1. In Twilio Console, go to Messaging > Try it out > Send a WhatsApp message
2. Or apply for WhatsApp Business API access
3. Set the WhatsApp webhook to `https://your-domain/api/whatsapp/webhook`

### Setting Up Proactive Calls

Schedule these endpoints to run periodically via cron:

```bash
# Generate reminders daily at 6 AM
0 6 * * * curl -X POST http://localhost:8000/api/proactive/generate

# Deliver pending messages every 30 minutes
*/30 * * * * curl -X POST http://localhost:8000/api/proactive/deliver?limit=20
```

### Health Check

```
GET /api/health

Response:
{
  "status": "ok",
  "service": "KisanVaani",
  "version": "2.1.0",
  "mock_mode": false,
  "database": "connected",
  "ai_configured": true,
  "twilio_configured": true
}
```

### Database

KisanVaani uses SQLite by default. Tables are auto-created on first run.

**Tables:**
- `call_logs` — All voice/text/WhatsApp interactions
- `farmer_profiles` — Farmer memory and profiles
- `farmer_expenses` — Voice-tracked expenses
- `crop_diary` — Farming activity log
- `crop_reminders` — Auto-generated reminders
- `alerts` — Proactive weather/pest/price alerts
- `community_insights` — Aggregated farmer intelligence
- `conversation_turns` — Persistent session history
- `whatsapp_messages` — WhatsApp message log
- `scheduled_calls` — Proactive outbound call queue
- `price_history` — Historical mandi prices (90 days seeded)
- `expert_callbacks` — Human expert escalation queue
- `farmer_questions` — Community peer Q&A
- `market_listings` — Buy/sell marketplace
- `satellite_reports` — NDVI crop health reports

For production with concurrent users, consider migrating to PostgreSQL by changing `DATABASE_URL`:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/kisanvaani
```

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

80 tests covering all features. Tests run in mock mode automatically.
