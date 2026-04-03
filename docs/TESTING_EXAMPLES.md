# KisanVaani — Sample Test Examples

Replace `BASE_URL` with your live Render URL (e.g., `https://kisanvaani.onrender.com`).

For local testing use: `http://localhost:8000`

---

## Quick Smoke Test (Browser)

Open these URLs directly in your browser:

```
{BASE_URL}/                          # Landing page
{BASE_URL}/demo                      # Voice demo (try the mic!)
{BASE_URL}/prices                    # Price prediction page
{BASE_URL}/satellite                 # Satellite monitoring page
{BASE_URL}/marketplace               # Farmer marketplace
{BASE_URL}/expert                    # Expert callback system
{BASE_URL}/network                   # Farmer community network
{BASE_URL}/features                  # All features demo
{BASE_URL}/alerts                    # Proactive alerts
{BASE_URL}/dashboard                 # Analytics dashboard
{BASE_URL}/calls                     # Call history
{BASE_URL}/api/health                # Health check (JSON)
{BASE_URL}/api/languages             # Supported languages
{BASE_URL}/docs                      # Swagger API docs (auto-generated)
```

---

## API Test Examples (curl)

### 1. Health Check
```bash
curl https://kisanvaani.onrender.com/api/health
```

Expected:
```json
{"status":"ok","service":"KisanVaani","version":"2.1.0","mock_mode":true,"database":"connected"}
```

---

### 2. Onboard a Farmer (Indian)
```bash
curl -X POST https://kisanvaani.onrender.com/api/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ramesh Patil",
    "language": "hi",
    "country": "IN",
    "region": "Maharashtra",
    "district": "Pune",
    "crops": ["Tomato", "Onion"],
    "land_acres": 3.5,
    "soil_type": "black",
    "irrigation_type": "drip"
  }'
```

Expected: farmer_id + welcome message + tips

---

### 3. Onboard a Kenyan Farmer
```bash
curl -X POST https://kisanvaani.onrender.com/api/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "name": "James Ochieng",
    "language": "en",
    "country": "KE",
    "region": "Western Kenya",
    "district": "Kakamega",
    "crops": ["Maize", "Beans"],
    "land_acres": 2
  }'
```

---

### 4. Ask Farming Question (Hindi)
```bash
curl -X POST https://kisanvaani.onrender.com/api/voice/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Mere tamatar ke patte peele ho rahe hain, kya karoon?",
    "language": "hi",
    "session_id": "test_hindi_1",
    "farmer_id": 1,
    "country": "IN"
  }'
```

Expected: Hindi AI response with specific dosages + audio URL

---

### 5. Ask in English (Kenya — Fall Armyworm)
```bash
curl -X POST https://kisanvaani.onrender.com/api/voice/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My maize has small holes in leaves and worms inside the whorl, what should I do?",
    "language": "en",
    "session_id": "test_english_1",
    "farmer_id": 2,
    "country": "KE"
  }'
```

---

### 6. Ask in Telugu
```bash
curl -X POST https://kisanvaani.onrender.com/api/voice/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Naa vari pantalo purugulu vasthunnaayi, emi cheyali?",
    "language": "te",
    "session_id": "test_telugu_1",
    "country": "IN"
  }'
```

---

### 7. Ask in Tamil
```bash
curl -X POST https://kisanvaani.onrender.com/api/voice/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "En nel payiril puzhu irukku, enna seyyanum?",
    "language": "ta",
    "session_id": "test_tamil_1",
    "country": "IN"
  }'
```

---

### 8. Ask in Swahili
```bash
curl -X POST https://kisanvaani.onrender.com/api/voice/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Mimea yangu ya mahindi yana wadudu, nifanye nini?",
    "language": "sw",
    "session_id": "test_swahili_1",
    "country": "KE"
  }'
```

---

### 9. Multi-Turn Conversation (Follow-up)
```bash
# Turn 1
curl -X POST https://kisanvaani.onrender.com/api/voice/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My cotton has white spots on the leaves",
    "language": "en",
    "session_id": "test_multiturn",
    "country": "IN"
  }'

# Turn 2 (same session_id — AI remembers cotton context)
curl -X POST https://kisanvaani.onrender.com/api/voice/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Should I spray in the morning or evening?",
    "language": "en",
    "session_id": "test_multiturn",
    "country": "IN"
  }'
```

---

### 10. Expense Auto-Detection
```bash
curl -X POST https://kisanvaani.onrender.com/api/voice/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Maine kal 3000 rupaye ka DAP khad kharida tomato ke liye",
    "language": "hi",
    "session_id": "test_expense",
    "farmer_id": 1,
    "country": "IN"
  }'
```

Expected: response_text + `expense_detected: {category: "fertilizer", amount: 3000, crop: "Tomato"}`

---

### 11. Weather Forecast
```bash
# Pune, India
curl https://kisanvaani.onrender.com/api/weather/pune

# Kakamega, Kenya
curl https://kisanvaani.onrender.com/api/weather/kakamega

# Kano, Nigeria
curl https://kisanvaani.onrender.com/api/weather/kano
```

---

### 12. AI Price Prediction
```bash
# Tomato — 14 day forecast
curl "https://kisanvaani.onrender.com/api/prices/predict/tomato?days=14"

# Wheat — 7 day forecast
curl "https://kisanvaani.onrender.com/api/prices/predict/wheat?days=7"

# Cotton — 28 day forecast
curl "https://kisanvaani.onrender.com/api/prices/predict/cotton?days=28"

# Price trends (30-day chart data)
curl "https://kisanvaani.onrender.com/api/prices/trends/Tomato?days=30"
```

---

### 13. Satellite Crop Health (NDVI)
```bash
# By location name
curl -X POST https://kisanvaani.onrender.com/api/satellite/analyze \
  -H "Content-Type: application/json" \
  -d '{"location": "pune", "crop": "Tomato", "farmer_id": 1}'

# By coordinates (Kakamega, Kenya)
curl -X POST https://kisanvaani.onrender.com/api/satellite/analyze \
  -H "Content-Type: application/json" \
  -d '{"latitude": 0.28, "longitude": 34.75, "crop": "Maize"}'

# Regional overview
curl "https://kisanvaani.onrender.com/api/satellite/regional/nagpur?crop=Cotton"
```

---

### 14. Soil Test Interpretation
```bash
# Low nutrients (poor soil)
curl -X POST https://kisanvaani.onrender.com/api/soil/interpret \
  -H "Content-Type: application/json" \
  -d '{
    "ph": 6.5,
    "nitrogen": 120,
    "phosphorus": 10,
    "potassium": 250,
    "organic_carbon": 0.4,
    "crop": "Tomato"
  }'

# Ideal soil
curl -X POST https://kisanvaani.onrender.com/api/soil/interpret \
  -H "Content-Type: application/json" \
  -d '{"ph": 6.8, "nitrogen": 350, "phosphorus": 40, "potassium": 250, "organic_carbon": 1.0}'

# Acidic soil
curl -X POST https://kisanvaani.onrender.com/api/soil/interpret \
  -H "Content-Type: application/json" \
  -d '{"ph": 4.2, "nitrogen": 80, "phosphorus": 5}'
```

---

### 15. Crop Insurance Auto-Claim
```bash
# First add a diary entry
curl -X POST https://kisanvaani.onrender.com/api/diary \
  -H "Content-Type: application/json" \
  -d '{
    "farmer_id": 1, "crop": "Tomato", "activity": "planted",
    "details": "500 seedlings in raised beds", "date": "2026-03-01"
  }'

# Add expense
curl -X POST https://kisanvaani.onrender.com/api/expenses \
  -H "Content-Type: application/json" \
  -d '{
    "farmer_id": 1, "category": "seeds", "amount": 3000,
    "description": "Tomato seedlings", "crop": "Tomato"
  }'

# Generate insurance claim
curl -X POST https://kisanvaani.onrender.com/api/insurance/claim \
  -H "Content-Type: application/json" \
  -d '{
    "farmer_id": 1,
    "crop": "Tomato",
    "damage_type": "pest",
    "damage_description": "Fall armyworm destroyed 60% of crop",
    "country": "IN"
  }'

# List insurance schemes
curl https://kisanvaani.onrender.com/api/insurance/schemes/IN
curl https://kisanvaani.onrender.com/api/insurance/schemes/KE
```

---

### 16. Expert Callback
```bash
# Request callback
curl -X POST https://kisanvaani.onrender.com/api/expert/request \
  -H "Content-Type: application/json" \
  -d '{
    "farmer_id": 1,
    "question": "My cow has fever and stopped eating for 2 days, udders are swollen",
    "ai_confidence": "low",
    "category": "livestock",
    "language": "hi",
    "country": "IN"
  }'

# View queue
curl "https://kisanvaani.onrender.com/api/expert/queue?status=pending"

# Resolve ticket (replace 1 with actual ticket_id)
curl -X POST https://kisanvaani.onrender.com/api/expert/1/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "expert_name": "Dr. Sharma, Veterinarian",
    "response": "Sounds like mastitis. Apply warm compress on udders. Give Paracetamol 10ml. Call vet if no improvement in 24 hours."
  }'

# Stats
curl https://kisanvaani.onrender.com/api/expert/stats
```

---

### 17. Farmer Marketplace
```bash
# Create sell listing
curl -X POST https://kisanvaani.onrender.com/api/marketplace/listings \
  -H "Content-Type: application/json" \
  -d '{
    "farmer_id": 1,
    "listing_type": "sell",
    "crop": "Tomato",
    "quantity": "15 quintals",
    "price_per_unit": 2500,
    "region": "Maharashtra",
    "description": "Fresh red tomatoes, Grade A, harvested yesterday"
  }'

# Create buy listing
curl -X POST https://kisanvaani.onrender.com/api/marketplace/listings \
  -H "Content-Type: application/json" \
  -d '{
    "farmer_id": 2,
    "listing_type": "buy",
    "crop": "Wheat",
    "quantity": "5 quintals",
    "region": "Western Kenya"
  }'

# Browse all
curl https://kisanvaani.onrender.com/api/marketplace/listings

# Filter by crop
curl "https://kisanvaani.onrender.com/api/marketplace/listings?crop=Tomato"

# Stats
curl https://kisanvaani.onrender.com/api/marketplace/stats
```

---

### 18. Community Network
```bash
# Share Q&A
curl -X POST https://kisanvaani.onrender.com/api/community/share \
  -H "Content-Type: application/json" \
  -d '{
    "region": "Maharashtra",
    "country": "IN",
    "crop": "Tomato",
    "question_summary": "White fungus at tomato roots, leaves yellowing",
    "ai_answer": "Fusarium Wilt. Apply Trichoderma viride 10g/liter at roots. Stop irrigation 2-3 days.",
    "category": "disease"
  }'

# Browse questions
curl "https://kisanvaani.onrender.com/api/community/questions?country=IN"

# Upvote (replace 1 with actual id)
curl -X POST https://kisanvaani.onrender.com/api/community/questions/1/helpful

# Trending topics
curl "https://kisanvaani.onrender.com/api/community/trending?country=IN"
```

---

### 19. Proactive Calls
```bash
# Generate reminders for all farmers
curl -X POST https://kisanvaani.onrender.com/api/proactive/generate

# Deliver pending
curl -X POST "https://kisanvaani.onrender.com/api/proactive/deliver?limit=10"

# View queue
curl https://kisanvaani.onrender.com/api/proactive/queue

# Stats
curl https://kisanvaani.onrender.com/api/proactive/stats
```

---

### 20. SMS Commands
```bash
# List SMS commands
curl https://kisanvaani.onrender.com/api/sms/commands

# Send SMS (mock mode)
curl -X POST https://kisanvaani.onrender.com/api/sms/send \
  -H "Content-Type: application/json" \
  -d '{"to": "+919876543210", "message": "KisanVaani: Tomato Rs 2200/quintal. Price rising 3%. HOLD."}'
```

---

### 21. Other Features
```bash
# Yield prediction
curl -X POST https://kisanvaani.onrender.com/api/yield/predict \
  -H "Content-Type: application/json" \
  -d '{"country": "IN", "crop": "wheat", "land_acres": 5, "soil_type": "loamy", "irrigation_type": "drip"}'

# Loan eligibility
curl https://kisanvaani.onrender.com/api/loans/IN
curl https://kisanvaani.onrender.com/api/loans/KE

# KVK locator
curl https://kisanvaani.onrender.com/api/kvk/IN/Maharashtra

# Pest gallery
curl https://kisanvaani.onrender.com/api/pests

# Alerts
curl https://kisanvaani.onrender.com/api/alerts

# Community insights
curl https://kisanvaani.onrender.com/api/community

# Crop diary
curl -X POST https://kisanvaani.onrender.com/api/diary \
  -H "Content-Type: application/json" \
  -d '{"farmer_id": 1, "crop": "Tomato", "activity": "irrigated", "details": "Drip irrigation 30 minutes"}'

curl https://kisanvaani.onrender.com/api/diary/1
curl https://kisanvaani.onrender.com/api/reminders/1

# Farmer report
curl https://kisanvaani.onrender.com/api/report/1

# Analytics
curl https://kisanvaani.onrender.com/api/analytics/overview
curl https://kisanvaani.onrender.com/api/analytics/languages
curl https://kisanvaani.onrender.com/api/analytics/timeline
curl https://kisanvaani.onrender.com/api/calls
```

---

## Browser Testing Checklist

Open your Render URL and test each page:

### Landing Page (`/`)
- [ ] Hero section loads with "Voice-First AI Farm Advisor"
- [ ] Feature cards visible
- [ ] "Try Demo" button works

### Voice Demo (`/demo`)
- [ ] Language selector works (Hindi, English, Telugu, Tamil, Swahili)
- [ ] Country selector works (India, Kenya, Nigeria, Ethiopia)
- [ ] Type a question and click Send
- [ ] Example questions are clickable
- [ ] AI response appears in chat
- [ ] Audio plays (or mock audio in mock mode)

### Price Prediction (`/prices`)
- [ ] Select crop (Tomato, Wheat, Cotton, etc.)
- [ ] Click "Predict Price"
- [ ] Price card shows current + predicted price
- [ ] Recommendation shows (HOLD/SELL/STABLE)
- [ ] Weekly forecast renders
- [ ] 30-day bar chart renders

### Satellite Monitoring (`/satellite`)
- [ ] Select location (Pune, Nagpur, Kakamega, etc.)
- [ ] Select crop
- [ ] Click "Analyze Field"
- [ ] NDVI ring gauge renders with score
- [ ] Health status shows (healthy/moderate/stressed/critical)
- [ ] Regional comparison appears
- [ ] Recommendations list renders

### Marketplace (`/marketplace`)
- [ ] Stats cards show (Total, Selling, Buying)
- [ ] Click "New Listing" → form appears
- [ ] Fill form and post → listing appears
- [ ] Filter by crop works
- [ ] Filter by type (sell/buy) works

### Expert Callback (`/expert`)
- [ ] Stats cards show
- [ ] "Request Callback" tab → fill form → submit
- [ ] Ticket created with ID
- [ ] "Expert Queue" tab → tickets visible
- [ ] "Respond" → resolve workflow works

### Farmer Network (`/network`)
- [ ] "Community Q&A" tab → questions visible
- [ ] Upvote button works
- [ ] "Trending" tab shows topics
- [ ] "Share Knowledge" tab → post Q&A
- [ ] Country/region filters work

### Features (`/features`)
- [ ] Weather: Enter "Pune" → get forecast
- [ ] Yield: Select crop + acres → predict
- [ ] Loans: Select country → see schemes
- [ ] KVK: Select region → find centers
- [ ] Pests: Gallery loads with treatments
- [ ] Diary: Add entry → see reminders

### Alerts (`/alerts`)
- [ ] Alert cards load (weather, pest, price)
- [ ] Community insights visible

### Dashboard (`/dashboard`)
- [ ] Stats cards render
- [ ] Language chart renders
- [ ] Timeline chart renders

### Call History (`/calls`)
- [ ] Call records appear after making voice queries

---

## Quick Full Test Script (copy-paste all at once)

```bash
BASE=https://kisanvaani.onrender.com

echo "=== Health ===" && curl -s $BASE/api/health | python3 -m json.tool

echo "=== Onboard ===" && curl -s -X POST $BASE/api/onboard \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo Farmer","language":"en","country":"IN","region":"Maharashtra","crops":["Tomato"],"land_acres":2}' | python3 -m json.tool

echo "=== Voice (English) ===" && curl -s -X POST $BASE/api/voice/text \
  -H "Content-Type: application/json" \
  -d '{"text":"My tomato leaves are turning yellow","language":"en","session_id":"demo1","country":"IN"}' | python3 -m json.tool

echo "=== Weather ===" && curl -s $BASE/api/weather/pune | python3 -m json.tool

echo "=== Price ===" && curl -s "$BASE/api/prices/predict/tomato?days=7" | python3 -m json.tool

echo "=== Satellite ===" && curl -s -X POST $BASE/api/satellite/analyze \
  -H "Content-Type: application/json" \
  -d '{"location":"pune","crop":"Tomato"}' | python3 -m json.tool

echo "=== Soil ===" && curl -s -X POST $BASE/api/soil/interpret \
  -H "Content-Type: application/json" \
  -d '{"ph":6.5,"nitrogen":120,"phosphorus":10}' | python3 -m json.tool

echo "=== Loans ===" && curl -s $BASE/api/loans/IN | python3 -m json.tool

echo "=== Pests ===" && curl -s $BASE/api/pests | python3 -m json.tool | head -20

echo "=== Alerts ===" && curl -s $BASE/api/alerts | python3 -m json.tool | head -20

echo "=== SMS Commands ===" && curl -s $BASE/api/sms/commands | python3 -m json.tool

echo "=== DONE ==="
```
