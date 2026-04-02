# KisanVaani — API Reference

Base URL: `http://localhost:8000/api`

All endpoints return JSON. Authentication is not required (add as needed for production).

---

## Voice & AI

### POST `/voice/text`
Process a text question through the AI pipeline.

**Request:**
```json
{
  "text": "Mere tamatar ke patte peele ho rahe hain",
  "language": "hi",           // hi, te, ta, sw, en, auto
  "session_id": "web_123",    // For multi-turn conversation
  "farmer_id": 1,             // Optional: enables farmer memory
  "country": "IN"             // IN, KE, NG, ET
}
```

**Response:**
```json
{
  "transcript": "Mere tamatar ke patte peele ho rahe hain",
  "response_text": "Aapke tamatar ke patte peele hone ka kaaran...",
  "audio_url": "/api/voice/audio/web_123_a1b2c3d4.wav",
  "language": "hi",
  "session_id": "web_123",
  "expense_detected": null
}
```

**Validation:**
- `text`: 1-2000 characters, cannot be empty
- `language`: must be hi, te, ta, sw, en, or auto
- `session_id`: max 100 characters
- Rate limit: 20/minute

---

### POST `/voice/photo`
Upload a crop photo for AI diagnosis.

**Request:** `multipart/form-data`
- `photo`: Image file (JPEG, PNG, WebP, HEIC, max 10MB)
- `text`: Description (default: "Please diagnose this crop problem")
- `language`: hi, te, ta, sw, en
- `session_id`: Session ID
- `farmer_id`: Optional farmer ID
- `country`: IN, KE, NG, ET

**Response:** Same as `/voice/text`

Rate limit: 10/minute

---

### GET `/voice/audio/{filename}`
Serve a generated audio file.

**Response:** Audio file (WAV or MP3)

---

## WhatsApp

### POST `/whatsapp/webhook`
Twilio WhatsApp webhook handler. Receives incoming messages and responds with TwiML.

**Request:** Twilio form data (Body, From, NumMedia, MediaUrl0, etc.)

**Response:** TwiML XML with AI response

---

### POST `/whatsapp/send`
Send an outbound WhatsApp message.

```json
{
  "to": "+919876543210",
  "message": "Your tomato needs irrigation today",
  "language": "en"
}
```

**Response:**
```json
{
  "status": "sent",
  "sid": "SM..."
}
```

---

### GET `/whatsapp/conversations/{farmer_id}`
Get WhatsApp conversation history.

**Query params:** `limit` (default 50)

---

## Price Prediction

### GET `/prices/predict/{crop}`
Predict future mandi price.

**Path:** `crop` — Crop name (wheat, tomato, rice, cotton, onion, etc.)

**Query params:** `days` (default 7, max 28), `country` (default IN)

**Response:**
```json
{
  "crop": "Tomato",
  "current_price": 2200,
  "predicted_price": 2267,
  "predicted_range": {"low": 1145, "high": 3389},
  "change_percent": 3.0,
  "days_ahead": 14,
  "recommendation": "HOLD (slight uptrend)",
  "reason": "Small price increase expected (~3%)...",
  "weekly_forecast": [
    {"week": 1, "date": "2026-04-09", "predicted_price": 2233},
    {"week": 2, "date": "2026-04-16", "predicted_price": 2267}
  ],
  "confidence": "high",
  "unit": "Rs/quintal",
  "method": "trend+seasonal"
}
```

---

### GET `/prices/trends/{crop}`
Historical price data for charts.

**Query params:** `days` (default 30)

**Response:**
```json
{
  "crop": "Wheat",
  "days": 30,
  "prices": [
    {"date": "2026-03-03", "price": 2310},
    {"date": "2026-03-04", "price": 2325}
  ]
}
```

---

## Satellite Monitoring

### POST `/satellite/analyze`
Analyze crop health from satellite data.

```json
{
  "latitude": 18.52,           // Either lat/lon
  "longitude": 73.86,
  "location": "pune",          // Or location name
  "crop": "Tomato",
  "farmer_id": 1,
  "country": "IN"
}
```

**Response:**
```json
{
  "ndvi_score": 0.52,
  "health_status": "moderate",
  "analysis": "Your tomato show moderate health (NDVI: 0.52)...",
  "location": {"latitude": 18.52, "longitude": 73.86},
  "regional_comparison": {
    "your_ndvi": 0.52,
    "region_average": 0.42,
    "comparison": "Your field is above the regional average"
  },
  "recommendations": ["Check soil moisture", "Consider foliar spray..."],
  "alert_level": "watch"
}
```

---

### GET `/satellite/history/{farmer_id}`
Satellite monitoring history. Query params: `limit` (default 10)

---

### GET `/satellite/regional/{location}`
Regional crop health overview. Query params: `crop`

---

## Expert Callbacks

### POST `/expert/request`
Request a human expert callback.

```json
{
  "farmer_id": 1,
  "question": "My cow has stopped giving milk",
  "ai_response": "This sounds like mastitis but I am not confident",
  "ai_confidence": "low",
  "category": "livestock",
  "language": "hi",
  "country": "IN",
  "region": "Maharashtra"
}
```

**Response:**
```json
{
  "ticket_id": 1,
  "status": "pending",
  "message": "You will receive a callback within 48 hours.",
  "priority": 1
}
```

---

### GET `/expert/queue`
View callback queue. Query params: `status`, `category`, `country`, `limit`

---

### POST `/expert/{ticket_id}/resolve`
```json
{
  "expert_name": "Dr. Sharma",
  "response": "This is mastitis. Apply warm compress and consult vet."
}
```

---

### GET `/expert/stats`
```json
{
  "total": 15,
  "pending": 3,
  "resolved": 12,
  "avg_resolution_hours": 18.5,
  "pending_by_category": {"livestock": 2, "disease": 1}
}
```

---

## Farmer Network

### POST `/community/share`
Share anonymized Q&A.

```json
{
  "region": "Maharashtra",
  "country": "IN",
  "crop": "Tomato",
  "question_summary": "How to control leaf curl virus?",
  "ai_answer": "Remove infected plants. Spray imidacloprid.",
  "category": "disease"
}
```

---

### GET `/community/questions`
Browse community Q&A. Query params: `region`, `country`, `crop`, `category`, `limit`

---

### POST `/community/questions/{id}/helpful`
Upvote a helpful answer.

---

### GET `/community/trending`
Trending topics. Query params: `country`, `days` (default 7)

---

## Marketplace

### POST `/marketplace/listings`
Create a buy/sell listing.

```json
{
  "farmer_id": 1,
  "listing_type": "sell",
  "crop": "Tomato",
  "quantity": "15 quintals",
  "price_per_unit": 2500,
  "region": "Maharashtra",
  "country": "IN",
  "description": "Fresh red tomatoes, Grade A"
}
```

---

### GET `/marketplace/listings`
Browse listings. Query params: `crop`, `region`, `country`, `listing_type`, `limit`

---

### GET `/marketplace/stats`
```json
{
  "total_listings": 25,
  "sell_listings": 18,
  "buy_listings": 7,
  "top_crops": {"Tomato": 8, "Wheat": 5, "Onion": 4}
}
```

---

## Proactive Calls

### POST `/proactive/generate`
Generate scheduled reminders for all farmers. Run daily via cron.

### POST `/proactive/deliver`
Deliver pending messages. Query params: `limit` (default 20). Run every 30 minutes.

### GET `/proactive/queue`
View queue. Query params: `status`, `farmer_id`, `limit`

### GET `/proactive/stats`
```json
{
  "total": 50,
  "pending": 12,
  "sent": 35,
  "failed": 3,
  "by_type": {"crop_reminder": 20, "weather_alert": 15, "price_alert": 10}
}
```

---

## Farmers

### POST `/onboard`
Quick onboarding with welcome tips.

### POST `/farmers`
Create farmer profile.

### GET `/farmers`
List farmers. Query params: `country`

### GET `/farmers/{id}`
Get farmer details.

### PUT `/farmers/{id}`
Update farmer profile.

### GET `/report/{farmer_id}`
Comprehensive farmer report (profile + expenses + diary + reminders + call history).

---

## Expenses

### POST `/expenses`
Log expense manually.

### GET `/expenses/{farmer_id}`
List farmer's expenses.

### GET `/expenses/{farmer_id}/summary`
Summary by category and crop.

---

## Features

### GET `/weather/{location}`
Weather forecast. Query params: `days` (default 3, max 7)

### GET `/kvk/{country}/{region}`
Find extension centers. Query params: `district`

### POST `/yield/predict`
Estimate crop yield.

### GET `/loans/{country}`
Loan schemes by country.

### GET `/pests`
List all pests.

### GET `/pests/{name}`
Pest details with treatments.

### POST `/diary`
Add crop diary entry.

### GET `/diary/{farmer_id}`
Get diary entries.

### GET `/reminders/{farmer_id}`
Pending and upcoming reminders. Query params: `days` (default 14)

---

## Alerts

### POST `/alerts`
Create alert.

### GET `/alerts`
List alerts. Query params: `country`, `active`

### GET `/community`
Community insights (aggregated regional intelligence).

---

## Analytics

### GET `/analytics/overview`
Dashboard summary stats.

### GET `/analytics/languages`
Language usage breakdown with percentages.

### GET `/analytics/timeline`
Daily call counts for last 30 days.

### GET `/calls`
Call history. Query params: `language`, `skip`, `limit`

---

## System

### GET `/health`
Health check with database, AI, and Twilio status.

### GET `/languages`
Supported languages with names and native names.

### GET `/countries`
Country data with languages and currency.
