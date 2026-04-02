# KisanVaani — Complete Feature Documentation

## Table of Contents

1. [Voice Pipeline & AI](#1-voice-pipeline--ai)
2. [WhatsApp Integration](#2-whatsapp-integration)
3. [Farmer Memory System](#3-farmer-memory-system)
4. [Photo Diagnosis](#4-photo-diagnosis)
5. [Expense Tracking](#5-expense-tracking)
6. [AI Price Predictor](#6-ai-price-predictor)
7. [Satellite Crop Monitoring](#7-satellite-crop-monitoring)
8. [Proactive Outbound Calls](#8-proactive-outbound-calls)
9. [Expert Callback System](#9-expert-callback-system)
10. [Farmer Community Network](#10-farmer-community-network)
11. [Marketplace](#11-marketplace)
12. [Weather Forecasts](#12-weather-forecasts)
13. [Crop Diary & Reminders](#13-crop-diary--reminders)
14. [Yield Predictor](#14-yield-predictor)
15. [Loan Eligibility](#15-loan-eligibility)
16. [KVK / Extension Center Locator](#16-kvk--extension-center-locator)
17. [Pest Gallery](#17-pest-gallery)
18. [Proactive Alerts](#18-proactive-alerts)
19. [Analytics Dashboard](#19-analytics-dashboard)

---

## 1. Voice Pipeline & AI

### How It Works
```
Farmer speaks/types question
        |
    Language detected (Hindi, Telugu, Tamil, Swahili, English)
        |
    Farming context built (country, season, crops, weather, farmer history)
        |
    Claude AI generates response (with retry logic, max 1000 tokens)
        |
    Expense auto-extracted if mentioned
        |
    Response cleaned -> TTS audio generated -> Played to farmer
```

### Supported Input Channels
- **Web Demo** — Browser mic recording via Web Speech API
- **Text Input** — Direct text via `/api/voice/text`
- **Phone Call** — Twilio IVR via `/api/twilio/incoming`
- **WhatsApp** — Text + photos via `/api/whatsapp/webhook`

### Multi-turn Conversations
Sessions are stored in SQLite (not in-memory). Each session retains the last 4 conversation turns, enabling follow-up questions like:
- Turn 1: "My tomato leaves are yellow"
- Turn 2: "What about the white spots near the roots?" (AI remembers the tomato context)

### Language Support
| Language | Code | STT | TTS | AI Response |
|----------|------|-----|-----|-------------|
| Hindi | hi | Web Speech API | Google Translate TTS | Full |
| Telugu | te | Web Speech API | Google Translate TTS | Full |
| Tamil | ta | Web Speech API | Google Translate TTS | Full |
| Swahili | sw | Web Speech API | Google Translate TTS | Full |
| English | en | Web Speech API | Google Translate TTS | Full |

### API
```
POST /api/voice/text
{
  "text": "Mere tamatar ke patte peele ho rahe hain",
  "language": "hi",
  "session_id": "unique_session_id",
  "farmer_id": 1,        // optional - enables farmer memory
  "country": "IN"
}

Response:
{
  "transcript": "...",
  "response_text": "...",    // AI farming advice
  "audio_url": "/api/voice/audio/filename.wav",
  "language": "hi",
  "session_id": "...",
  "expense_detected": null   // or {category, amount, description, crop}
}
```

---

## 2. WhatsApp Integration

### How It Works
Farmers send a message on WhatsApp to the KisanVaani number. The system:
1. Receives the message via Twilio WhatsApp webhook
2. Auto-detects language from script (Devanagari = Hindi, Telugu script, etc.)
3. Creates or retrieves farmer profile from phone hash
4. Processes text/photo through the same AI pipeline
5. Sends response back via WhatsApp

### Supported Message Types
- **Text** — Regular farming questions
- **Image** — Crop photos for diagnosis (auto-downloaded, base64 encoded, sent to Claude Vision)
- **Outbound** — Proactive alerts, reminders, and follow-ups

### API
```
POST /api/whatsapp/webhook      # Twilio webhook (incoming messages)
GET  /api/whatsapp/webhook      # Webhook verification
POST /api/whatsapp/send          # Send outbound message
GET  /api/whatsapp/conversations/{farmer_id}  # Chat history
```

### Setup
1. Configure Twilio WhatsApp Sandbox or Business API
2. Set webhook URL to `https://your-domain/api/whatsapp/webhook`
3. Add Twilio credentials to `.env`

---

## 3. Farmer Memory System

### What's Stored
| Field | Example |
|-------|---------|
| Name | Ramesh Patil |
| Phone hash | sha256(phone)[:16] |
| Language | hi |
| Country | IN |
| Region/District/Village | Maharashtra / Pune / Shirur |
| Land size | 3.5 acres |
| Crops | ["Tomato", "Onion", "Soybean"] |
| Soil type | black |
| Irrigation | drip |
| Past problems | ["fusarium_wilt_tomato_2026"] |
| Active issues | ["yellowing_leaves"] |
| Last advice | "Apply Trichoderma viride..." |
| Total calls | 12 |

### How AI Uses Memory
Every AI call includes the farmer's full profile in the context. This enables:
- "Welcome back Ramesh! How is your tomato doing since the Fusarium issue?"
- Region-specific advice (Maharashtra weather, local KVK)
- Crop-specific dosages and schedules
- Referencing past problems and treatments

### API
```
POST /api/onboard              # Quick onboarding
POST /api/farmers              # Create profile
GET  /api/farmers/{id}         # Get profile
PUT  /api/farmers/{id}         # Update profile
GET  /api/report/{farmer_id}   # Full report with diary + expenses + history
```

---

## 4. Photo Diagnosis

### How It Works
1. Farmer uploads crop photo (JPEG, PNG, WebP, HEIC - max 10MB)
2. Image is base64-encoded and sent to Claude Vision
3. AI analyzes: leaf color, spots, insect presence, damage patterns, wilting
4. Combined with text description for holistic diagnosis
5. Returns disease identification + treatment with exact dosages

### API
```
POST /api/voice/photo
  - photo: (file upload)
  - text: "What is wrong with my plant?"
  - language: "en"
  - session_id: "..."
  - farmer_id: 1
  - country: "IN"
```

### Via WhatsApp
Farmers simply send a photo on WhatsApp with an optional caption. The system automatically processes it through Claude Vision.

---

## 5. Expense Tracking

### Auto-Detection
When a farmer says something like:
- "I spent 2000 on urea" -> Detected as fertilizer, Rs 2000
- "Pesticide cost me 500 for cotton" -> Detected as pesticide, Rs 500, crop: cotton

The AI extracts a JSON block:
```json
{"category": "fertilizer", "amount": 2000, "description": "Urea", "crop": "Tomato"}
```

This is automatically logged and removed from the spoken response.

### Categories
seeds, fertilizer, pesticide, labor, irrigation, equipment, transport, other

### API
```
POST /api/expenses                        # Manual logging
GET  /api/expenses/{farmer_id}            # List expenses
GET  /api/expenses/{farmer_id}/summary    # Summary by category & crop
```

### Example Summary Response
```json
{
  "total_spent": 12500,
  "by_category": {
    "fertilizer": 5000,
    "pesticide": 3500,
    "seeds": 2000,
    "labor": 2000
  },
  "by_crop": {
    "Tomato": 8000,
    "Onion": 4500
  },
  "expense_count": 8
}
```

---

## 6. AI Price Predictor

### Algorithm
1. Loads 90 days of historical price data (seeded on first run)
2. Calculates linear trend (regression slope) from last 30 days
3. Applies seasonal adjustment for the target month
4. Adds confidence interval based on crop volatility
5. Generates HOLD/SELL/SELL NOW recommendation

### Seasonal Patterns
Prices follow known agricultural cycles:
- Tomato: Peak in June-August (monsoon supply shortage)
- Wheat: Low post-harvest (March-April), rises through the year
- Onion: Volatile, peaks in July-September

### Recommendation Logic
| Price Change | Recommendation |
|-------------|---------------|
| > +10% | HOLD — prices rising, wait to sell |
| +3% to +10% | HOLD (slight uptrend) |
| -3% to +3% | STABLE — sell when ready |
| -10% to -3% | SELL SOON |
| < -10% | SELL NOW — prices dropping |

### API
```
GET /api/prices/predict/tomato?days=14

Response:
{
  "crop": "Tomato",
  "current_price": 2200,
  "predicted_price": 2267,
  "predicted_range": {"low": 1145, "high": 3389},
  "change_percent": 3.0,
  "recommendation": "HOLD (slight uptrend)",
  "reason": "Small price increase expected (~3%). Can wait if storage is available.",
  "weekly_forecast": [...],
  "confidence": "high",
  "unit": "Rs/quintal"
}

GET /api/prices/trends/wheat?days=30   # Historical trend data for charts
```

---

## 7. Satellite Crop Monitoring

### NDVI (Normalized Difference Vegetation Index)
| NDVI Range | Health Status | What It Means |
|-----------|--------------|---------------|
| 0.6 - 1.0 | Healthy | Dense, healthy vegetation |
| 0.4 - 0.6 | Moderate | Early stress or sparse vegetation |
| 0.2 - 0.4 | Stressed | Water deficit, nutrient deficiency, or pest damage |
| < 0.2 | Critical | Severe stress, crop failure, or bare soil |

### Data Source
Uses Open-Meteo evapotranspiration data as a vegetation proxy, with seasonal and geographic adjustments. In production, can be upgraded to Sentinel Hub Statistical API for real Sentinel-2 satellite imagery.

### Features
- **Field-level analysis** by coordinates or location name
- **Regional comparison** — your field vs regional average
- **Historical tracking** — monitor NDVI over time
- **Auto-recommendations** based on stress level

### API
```
POST /api/satellite/analyze
{
  "location": "pune",        // or use latitude/longitude
  "crop": "Tomato",
  "farmer_id": 1,
  "country": "IN"
}

Response:
{
  "ndvi_score": 0.52,
  "health_status": "moderate",
  "analysis": "Your tomato show moderate health...",
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

## 8. Proactive Outbound Calls

### Trigger Types
| Type | Example | Frequency |
|------|---------|-----------|
| Crop reminder | "Day 32: Time for pest check on your Tomato" | Based on crop diary |
| Weather alert | "Heavy rain expected tomorrow — delay pesticide spray" | When alert matches farmer |
| Price alert | "Tomato prices up 15% — good time to sell" | When price spikes |
| Scheme deadline | "PM-KISAN registration closes April 15" | Before deadlines |

### Smart Scheduling
1. `/api/proactive/generate` — Scans all farmers' crop diaries and active alerts
2. Generates personalized reminders in the farmer's language
3. Checks for duplicates (won't re-send same alert)
4. `/api/proactive/deliver` — Sends pending messages via WhatsApp/voice
5. Retries up to 3 times on failure

### Message Templates
Available in all 5 languages. Example (Hindi):
> "Namaste Ramesh ji! Aapke Tomato ko pest check ka samay aa gaya hai. Day 32: Check leaf undersides for insects. Spray neem oil if found. Koi sawaal ho toh KisanVaani ko call karein."

### API
```
POST /api/proactive/generate    # Generate reminders for all farmers
POST /api/proactive/deliver     # Send pending messages
GET  /api/proactive/queue       # View scheduled calls
GET  /api/proactive/stats       # Statistics
```

---

## 9. Expert Callback System

### Flow
```
Farmer asks complex question
        |
    AI responds but flags low confidence
        |
    Ticket created in expert queue (priority 1-3)
        |
    Expert views queue, picks ticket
        |
    Expert writes response
        |
    Response delivered to farmer via WhatsApp/call
```

### Priority Levels
| Priority | Category | SLA |
|----------|----------|-----|
| 1 (Urgent) | Livestock, severe disease | 24 hours |
| 2 (Normal) | Pest, soil, general farming | 48 hours |
| 3 (Low) | Information, schemes | 72 hours |

### API
```
POST /api/expert/request
{
  "farmer_id": 1,
  "question": "My cow has fever and swollen udders",
  "ai_confidence": "low",
  "category": "livestock",
  "language": "hi"
}

GET  /api/expert/queue?status=pending
POST /api/expert/{ticket_id}/resolve
GET  /api/expert/stats
```

---

## 10. Farmer Community Network

### Peer Q&A Sharing
Farmers' questions and AI answers are anonymized and shared with the community. Other farmers in the same region can see:
- "47 farmers in Western Kenya asked about fall armyworm this week"
- "Most effective treatment: neem oil 5ml/liter spray in the morning"

### Features
- **Share** — Auto-share (or manual) Q&A to community
- **Browse** — Filter by region, crop, category
- **Upvote** — Mark answers as helpful
- **Trending** — See most-reported topics in your area

### API
```
POST /api/community/share                      # Share Q&A
GET  /api/community/questions?region=Maharashtra # Browse
POST /api/community/questions/{id}/helpful      # Upvote
GET  /api/community/trending?country=IN         # Trending topics
```

---

## 11. Marketplace

### How It Works
Farmers create buy or sell listings for their produce. Buyers (other farmers, traders, FPOs) browse and contact directly — no middleman.

### Listing Fields
- Type: sell or buy
- Crop, quantity (e.g., "15 quintals"), expected price
- Region, district, country
- Contact phone number
- Description
- Auto-expires after 30 days

### API
```
POST /api/marketplace/listings
{
  "farmer_id": 1,
  "listing_type": "sell",
  "crop": "Tomato",
  "quantity": "15 quintals",
  "price_per_unit": 2500,
  "region": "Maharashtra"
}

GET /api/marketplace/listings?crop=Tomato&region=Maharashtra
GET /api/marketplace/stats
```

---

## 12. Weather Forecasts

### Data Source
Open-Meteo API — free, no API key needed, covers 20+ farming regions across India, Kenya, Nigeria, and Ethiopia.

### Response Includes
- Current temperature, condition, wind speed
- 7-day forecast: max/min temp, rain probability, precipitation amount

### API
```
GET /api/weather/pune

Response:
{
  "location": "pune",
  "current": {"temperature": 22.9, "condition": "Clear sky", "windspeed": 2.1},
  "forecast": [
    {"date": "2026-04-03", "temp_max": 34.2, "temp_min": 21.0, "rain_mm": 0.0, "rain_chance": 18}
  ]
}
```

---

## 13. Crop Diary & Reminders

### Activities Tracked
planted, irrigated, fertilized, sprayed, harvested, weeded, sold

### Auto-generated Reminders
When a farmer logs "planted Tomato on March 1", the system auto-generates:
| Day | Reminder |
|-----|---------|
| Day 7 | Irrigation check |
| Day 21-25 | First fertilizer dose (urea 50kg/acre) |
| Day 28-32 | Pest inspection |
| Day 45-50 | Second fertilizer (DAP + potash) |
| Day 65-70 | Harvest preparation (for tomato ~75 days) |

### API
```
POST /api/diary            # Add diary entry
GET  /api/diary/{farmer_id}       # Get diary entries
GET  /api/reminders/{farmer_id}   # Get pending + upcoming reminders
```

---

## 14. Yield Predictor

### Inputs
- Country, crop, land area (acres), soil type, irrigation type

### Adjustment Factors
- Drip irrigation: +25%
- Regular irrigation: +15%
- Good soil (loamy/black): +10%
- Sandy soil: -10%

### API
```
POST /api/yield/predict
{
  "country": "IN",
  "crop": "wheat",
  "land_acres": 2,
  "soil_type": "loamy",
  "irrigation_type": "drip"
}
```

---

## 15. Loan Eligibility

### Schemes by Country
**India:**
- KCC (Kisan Credit Card) — Rs 3 lakh at 4%
- PM-KISAN — Rs 6,000/year free
- PMFBY — Crop insurance
- AIF — Agricultural Infrastructure Fund
- Soil Health Card

**Kenya:** AFC loans (KES 5M)
**Nigeria:** Anchor Borrowers (NGN 500K at 9%), Growth Enhancement Support
**Ethiopia:** PSNP, Agricultural Growth Program

### API
```
GET /api/loans/IN   # Indian schemes
GET /api/loans/KE   # Kenyan schemes
```

---

## 16. KVK / Extension Center Locator

Finds the nearest Krishi Vigyan Kendra (India) or county extension office (Kenya/Nigeria/Ethiopia) based on country and region.

### API
```
GET /api/kvk/IN/Maharashtra
```

---

## 17. Pest Gallery

Database of common pests with:
- Common names (Hindi + English)
- Affected crops
- Symptom descriptions
- Organic + chemical treatment options with exact dosages
- Image references

### API
```
GET /api/pests              # List all
GET /api/pests/bollworm     # Details for specific pest
```

---

## 18. Proactive Alerts

### Alert Types
- **Weather** — Heavy rain, drought, frost warnings (source: IMD, NiMet, Open-Meteo)
- **Pest outbreak** — Regional pest infestation warnings
- **Price spike** — Mandi price jumps for specific crops
- **Scheme deadline** — Government registration deadlines

### Community Insights
Aggregated intelligence from farmer queries:
- "23 farmers in Vidarbha reported bollworm this week"
- "Rice blast spreading in Telangana due to humid weather"

### API
```
POST /api/alerts          # Create alert
GET  /api/alerts?country=IN&active=true  # List alerts
GET  /api/community       # Community insights
```

---

## 19. Analytics Dashboard

### Overview Stats
- Total calls, unique sessions, languages served, calls today

### Visualizations
- Call timeline (30-day bar chart)
- Language breakdown (pie chart)
- Call history with search and pagination

### API
```
GET /api/analytics/overview     # Summary stats
GET /api/analytics/languages    # Language breakdown
GET /api/analytics/timeline     # Daily counts
GET /api/calls?language=hi&skip=0&limit=20  # Call history
```
