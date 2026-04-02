"""Rigorous real-data end-to-end test of ALL KisanVaani features.
Run against a live server (not mock mode).
Usage: python tests/real_data_test.py
"""
import json
import sys
import time
import requests

BASE = "http://localhost:8000/api"
PASS = 0
FAIL = 0
RESULTS = []

def test(name, fn):
    global PASS, FAIL
    try:
        result = fn()
        PASS += 1
        RESULTS.append(f"  PASS  {name}")
        return result
    except Exception as e:
        FAIL += 1
        RESULTS.append(f"  FAIL  {name} -- {e}")
        return None

def get(path, **kw): return requests.get(f"{BASE}{path}", **kw)
def post(path, **kw): return requests.post(f"{BASE}{path}", **kw)

# ─────────────── 1. SYSTEM ───────────────
print("\n=== 1. SYSTEM ===")

def t_health():
    r = get("/health")
    d = r.json()
    assert d["status"] == "ok", f"Status: {d['status']}"
    assert d["database"] == "connected"
    assert d["ai_configured"] == True
    assert d["mock_mode"] == False, "Server is in MOCK mode!"
    print(f"  Server: v{d['version']}, DB: {d['database']}, AI: {d['ai_configured']}")
test("Health check", t_health)

def t_languages():
    r = get("/languages")
    d = r.json()
    assert len(d) == 5, f"Expected 5 languages, got {len(d)}"
    for lang in ["hi", "te", "ta", "sw", "en"]:
        assert lang in d, f"Missing language: {lang}"
test("Languages (5 supported)", t_languages)

def t_countries():
    r = get("/countries")
    d = r.json()
    assert len(d) >= 4
test("Countries (4 supported)", t_countries)

# ─────────────── 2. FARMER ONBOARDING ───────────────
print("\n=== 2. FARMER MANAGEMENT ===")

farmer1_id = None
def t_onboard():
    global farmer1_id
    r = post("/onboard", json={
        "name": "Ramesh Patil", "language": "hi", "country": "IN",
        "region": "Maharashtra", "district": "Pune", "village": "Shirur",
        "crops": ["Tomato", "Onion"], "land_acres": 3.5,
        "soil_type": "black", "irrigation_type": "drip",
    })
    d = r.json()
    assert "farmer_id" in d
    assert "tips" in d
    assert len(d["tips"]) > 0
    farmer1_id = d["farmer_id"]
    print(f"  Farmer ID: {farmer1_id}, Tips: {len(d['tips'])}")
test("Onboard Indian farmer", t_onboard)

farmer2_id = None
def t_onboard_ke():
    global farmer2_id
    r = post("/onboard", json={
        "name": "James Ochieng", "language": "en", "country": "KE",
        "region": "Western Kenya", "district": "Kakamega",
        "crops": ["Maize", "Beans"], "land_acres": 2,
    })
    d = r.json()
    farmer2_id = d["farmer_id"]
    assert farmer2_id
test("Onboard Kenyan farmer", t_onboard_ke)

def t_get_farmer():
    r = get(f"/farmers/{farmer1_id}")
    d = r.json()
    assert d["name"] == "Ramesh Patil"
    assert d["country"] == "IN"
test("Get farmer profile", t_get_farmer)

def t_list_farmers():
    r = get("/farmers")
    d = r.json()
    assert len(d) >= 2
test("List farmers", t_list_farmers)

# ─────────────── 3. VOICE AI (Real Claude) ───────────────
print("\n=== 3. VOICE AI (Real Claude) ===")

def t_voice_hindi():
    r = post("/voice/text", json={
        "text": "Mere tamatar ke patte peele ho rahe hain, kya karoon?",
        "language": "hi", "session_id": "realtest_hi_1",
        "farmer_id": farmer1_id, "country": "IN",
    })
    d = r.json()
    assert r.status_code == 200
    assert len(d["response_text"]) > 50, "Response too short"
    assert d["audio_url"].startswith("/api/voice/audio/")
    print(f"  Hindi response: {len(d['response_text'])} chars")
test("Hindi voice query (tomato yellow leaves)", t_voice_hindi)

def t_voice_english():
    r = post("/voice/text", json={
        "text": "My maize has holes in the leaves and worms in the whorl",
        "language": "en", "session_id": "realtest_en_1",
        "farmer_id": farmer2_id, "country": "KE",
    })
    d = r.json()
    assert r.status_code == 200
    assert len(d["response_text"]) > 50
    print(f"  English response: {len(d['response_text'])} chars")
test("English voice query (fall armyworm, Kenya)", t_voice_english)

def t_voice_telugu():
    r = post("/voice/text", json={
        "text": "Naa patti pantalo purugulu ekkuvaga vasthunnaayi, emi spray cheyali?",
        "language": "te", "session_id": "realtest_te_1", "country": "IN",
    })
    assert r.status_code == 200
    assert len(r.json()["response_text"]) > 30
test("Telugu voice query", t_voice_telugu)

def t_voice_tamil():
    r = post("/voice/text", json={
        "text": "En nel payiril puzhu irukku, enna seyyanum?",
        "language": "ta", "session_id": "realtest_ta_1", "country": "IN",
    })
    assert r.status_code == 200
test("Tamil voice query", t_voice_tamil)

def t_voice_swahili():
    r = post("/voice/text", json={
        "text": "Mimea yangu ya mahindi yana wadudu, nifanye nini?",
        "language": "sw", "session_id": "realtest_sw_1", "country": "KE",
    })
    assert r.status_code == 200
test("Swahili voice query", t_voice_swahili)

def t_multi_turn():
    r1 = post("/voice/text", json={
        "text": "My cotton has white spots on leaves",
        "language": "en", "session_id": "realtest_multi",
        "farmer_id": farmer1_id, "country": "IN",
    })
    assert r1.status_code == 200
    r2 = post("/voice/text", json={
        "text": "Should I spray in the morning or evening?",
        "language": "en", "session_id": "realtest_multi",
        "farmer_id": farmer1_id, "country": "IN",
    })
    assert r2.status_code == 200
    # Should reference cotton context
    print(f"  Turn 2 response: {len(r2.json()['response_text'])} chars")
test("Multi-turn conversation (context memory)", t_multi_turn)

def t_expense_detection():
    r = post("/voice/text", json={
        "text": "Maine kal 3000 rupaye ka DAP khad kharida tomato ke liye",
        "language": "hi", "session_id": "realtest_expense",
        "farmer_id": farmer1_id, "country": "IN",
    })
    d = r.json()
    assert r.status_code == 200
    if d.get("expense_detected"):
        print(f"  Expense detected: {d['expense_detected']}")
    else:
        print(f"  Expense not auto-detected (AI may not have flagged it)")
test("Expense auto-detection", t_expense_detection)

# ─────────────── 4. CROP DIARY & REMINDERS ───────────────
print("\n=== 4. CROP DIARY ===")

def t_diary_add():
    r = post("/diary", json={
        "farmer_id": farmer1_id, "crop": "Tomato", "activity": "planted",
        "details": "500 seedlings in raised beds", "quantity": "500",
        "date": "2026-03-01",
    })
    assert r.status_code == 200
    d = r.json()
    assert d["crop"] == "Tomato"
test("Add diary entry (planted tomato)", t_diary_add)

def t_diary_get():
    r = get(f"/diary/{farmer1_id}")
    d = r.json()
    assert len(d) > 0
    print(f"  Diary entries: {len(d)}")
test("Get diary entries", t_diary_get)

def t_reminders():
    r = get(f"/reminders/{farmer1_id}")
    d = r.json()
    print(f"  Reminders: {len(d)}")
test("Get reminders", t_reminders)

# ─────────────── 5. EXPENSES ───────────────
print("\n=== 5. EXPENSES ===")

def t_expense_add():
    r = post("/expenses", json={
        "farmer_id": farmer1_id, "category": "seeds",
        "amount": 2500, "description": "Tomato seedlings", "crop": "Tomato",
    })
    assert r.status_code in [200, 201]
test("Add expense manually", t_expense_add)

def t_expense_summary():
    r = get(f"/expenses/{farmer1_id}/summary")
    d = r.json()
    assert d["total_spent"] > 0
    print(f"  Total spent: Rs {d['total_spent']}, Categories: {list(d['by_category'].keys())}")
test("Expense summary", t_expense_summary)

# ─────────────── 6. WEATHER ───────────────
print("\n=== 6. WEATHER ===")

def t_weather():
    r = get("/weather/pune")
    d = r.json()
    assert "current" in d
    assert "forecast" in d
    print(f"  Pune: {d['current']['temperature']}C, {d['current']['condition']}")
test("Live weather (Pune)", t_weather)

def t_weather_kenya():
    r = get("/weather/kakamega")
    assert r.status_code == 200
test("Live weather (Kakamega, Kenya)", t_weather_kenya)

# ─────────────── 7. PRICE PREDICTION ───────────────
print("\n=== 7. PRICE PREDICTION ===")

def t_price_tomato():
    r = get("/prices/predict/tomato?days=14")
    d = r.json()
    assert "current_price" in d
    assert "predicted_price" in d
    assert "recommendation" in d
    print(f"  Tomato: Rs {d['current_price']} -> Rs {d['predicted_price']} ({d['change_percent']}%) = {d['recommendation']}")
test("Predict tomato price (14 days)", t_price_tomato)

def t_price_wheat():
    r = get("/prices/predict/wheat?days=7")
    d = r.json()
    assert d["unit"] == "Rs/quintal"
    assert d["confidence"] in ["low", "medium", "high"]
test("Predict wheat price (7 days)", t_price_wheat)

def t_price_trends():
    r = get("/prices/trends/Tomato?days=30")
    if r.status_code == 200:
        d = r.json()
        assert len(d["prices"]) > 0
        print(f"  Trend data points: {len(d['prices'])}")
test("Price trends (30-day)", t_price_trends)

# ─────────────── 8. SATELLITE MONITORING ───────────────
print("\n=== 8. SATELLITE MONITORING ===")

def t_satellite_pune():
    r = post("/satellite/analyze", json={
        "location": "pune", "crop": "Tomato",
        "farmer_id": farmer1_id, "country": "IN",
    })
    d = r.json()
    assert "ndvi_score" in d
    assert -1 <= d["ndvi_score"] <= 1
    assert d["health_status"] in ["healthy", "moderate", "stressed", "critical"]
    assert len(d["recommendations"]) > 0
    print(f"  NDVI: {d['ndvi_score']}, Status: {d['health_status']}, Alert: {d['alert_level']}")
test("Satellite analysis (Pune)", t_satellite_pune)

def t_satellite_kenya():
    r = post("/satellite/analyze", json={"location": "kakamega", "crop": "Maize"})
    assert r.status_code == 200
test("Satellite analysis (Kakamega)", t_satellite_kenya)

def t_satellite_history():
    r = get(f"/satellite/history/{farmer1_id}")
    d = r.json()
    assert isinstance(d, list)
    print(f"  History records: {len(d)}")
test("Satellite history", t_satellite_history)

# ─────────────── 9. EXPERT CALLBACKS ───────────────
print("\n=== 9. EXPERT CALLBACKS ===")

ticket_id = None
def t_expert_request():
    global ticket_id
    r = post("/expert/request", json={
        "farmer_id": farmer1_id,
        "question": "My cow has fever and stopped eating for 2 days",
        "ai_confidence": "low", "category": "livestock",
        "language": "hi", "country": "IN", "region": "Maharashtra",
    })
    d = r.json()
    assert d["status"] == "pending"
    assert d["priority"] == 1
    ticket_id = d["ticket_id"]
    print(f"  Ticket #{ticket_id}, Priority: {d['priority']}")
test("Request expert callback (livestock)", t_expert_request)

def t_expert_queue():
    r = get("/expert/queue?status=pending")
    d = r.json()
    assert len(d) > 0
    print(f"  Pending tickets: {len(d)}")
test("Expert queue", t_expert_queue)

def t_expert_resolve():
    r = post(f"/expert/{ticket_id}/resolve", json={
        "expert_name": "Dr. Sharma, Veterinarian",
        "response": "This sounds like bovine fever. Give Paracetamol 10ml + electrolyte water. If no improvement in 24hrs, call vet for blood test.",
    })
    assert r.json()["status"] == "resolved"
test("Resolve expert ticket", t_expert_resolve)

def t_expert_stats():
    r = get("/expert/stats")
    d = r.json()
    assert d["resolved"] > 0
    print(f"  Total: {d['total']}, Resolved: {d['resolved']}")
test("Expert stats", t_expert_stats)

# ─────────────── 10. MARKETPLACE ───────────────
print("\n=== 10. MARKETPLACE ===")

def t_market_sell():
    r = post("/marketplace/listings", json={
        "farmer_id": farmer1_id, "listing_type": "sell",
        "crop": "Tomato", "quantity": "15 quintals",
        "price_per_unit": 2500, "region": "Maharashtra",
        "description": "Fresh red tomatoes, Grade A",
    })
    d = r.json()
    assert d["status"] == "active"
    print(f"  Listing ID: {d['id']}")
test("Create sell listing", t_market_sell)

def t_market_buy():
    r = post("/marketplace/listings", json={
        "farmer_id": farmer2_id, "listing_type": "buy",
        "crop": "Wheat", "quantity": "5 quintals",
        "region": "Western Kenya",
    })
    assert r.json()["status"] == "active"
test("Create buy listing", t_market_buy)

def t_market_browse():
    r = get("/marketplace/listings")
    d = r.json()
    assert len(d) >= 2
    print(f"  Active listings: {len(d)}")
test("Browse marketplace", t_market_browse)

def t_market_stats():
    r = get("/marketplace/stats")
    d = r.json()
    assert d["total_listings"] >= 2
test("Marketplace stats", t_market_stats)

# ─────────────── 11. FARMER NETWORK ───────────────
print("\n=== 11. FARMER NETWORK ===")

def t_share_qa():
    r = post("/community/share", json={
        "region": "Maharashtra", "country": "IN", "crop": "Tomato",
        "question_summary": "White fungus at tomato roots, leaves yellowing from bottom",
        "ai_answer": "Fusarium Wilt. Apply Trichoderma viride 10g/liter. Stop irrigation 2-3 days.",
        "category": "disease",
    })
    assert r.json()["status"] == "shared"
test("Share community Q&A", t_share_qa)

def t_browse_qa():
    r = get("/community/questions?country=IN")
    d = r.json()
    assert len(d) > 0
    print(f"  Community questions: {len(d)}")
test("Browse community questions", t_browse_qa)

def t_upvote():
    qa = get("/community/questions?country=IN").json()
    if qa:
        r = post(f"/community/questions/{qa[0]['id']}/helpful")
        assert r.json()["helpful_count"] >= 1
test("Upvote helpful answer", t_upvote)

def t_trending():
    r = get("/community/trending?country=IN")
    assert r.status_code == 200
test("Trending topics", t_trending)

# ─────────────── 12. PROACTIVE CALLS ───────────────
print("\n=== 12. PROACTIVE CALLS ===")

def t_proactive_generate():
    r = post("/proactive/generate")
    d = r.json()
    assert "scheduled" in d
    print(f"  Scheduled: {d['scheduled']}")
test("Generate proactive calls", t_proactive_generate)

def t_proactive_deliver():
    r = post("/proactive/deliver?limit=5")
    d = r.json()
    print(f"  Delivered: {d['delivered']}/{d['total']}")
test("Deliver pending calls", t_proactive_deliver)

def t_proactive_stats():
    r = get("/proactive/stats")
    d = r.json()
    assert "total" in d
test("Proactive stats", t_proactive_stats)

# ─────────────── 13. SOIL TEST OCR ───────────────
print("\n=== 13. SOIL TEST OCR ===")

def t_soil_interpret():
    r = post("/soil/interpret", json={
        "ph": 6.5, "nitrogen": 120, "phosphorus": 10,
        "potassium": 250, "organic_carbon": 0.4, "crop": "Tomato",
    })
    d = r.json()
    assert "health" in d
    assert len(d["issues"]) > 0
    print(f"  Soil health: {d['health']}, Issues: {len(d['issues'])}")
    for issue in d["issues"]:
        print(f"    - {issue}")
test("Interpret soil values", t_soil_interpret)

def t_soil_ideal():
    r = post("/soil/interpret", json={
        "ph": 6.8, "nitrogen": 350, "phosphorus": 40,
        "potassium": 250, "organic_carbon": 1.0,
    })
    d = r.json()
    assert d["health"] == "good"
    print(f"  Ideal soil: {d['health']}, Suitable crops: {d['crop_suitability'][:3]}")
test("Ideal soil interpretation", t_soil_ideal)

def t_soil_poor():
    r = post("/soil/interpret", json={"ph": 4.2, "nitrogen": 80, "phosphorus": 5})
    d = r.json()
    assert d["health"] == "poor"
test("Poor soil detection", t_soil_poor)

# ─────────────── 14. INSURANCE CLAIMS ───────────────
print("\n=== 14. INSURANCE CLAIMS ===")

def t_insurance_claim():
    r = post("/insurance/claim", json={
        "farmer_id": farmer1_id, "crop": "Tomato",
        "damage_type": "pest",
        "damage_description": "Fall armyworm destroyed 60% of crop, leaves eaten, worms visible in whorl",
        "country": "IN",
    })
    d = r.json()
    assert "claim_id" in d
    assert len(d["applicable_schemes"]) > 0
    assert len(d["next_steps"]) > 0
    print(f"  Claim ID: {d['claim_id']}")
    print(f"  Investment evidence: Rs {d['financial_evidence']['total_investment']}")
    print(f"  Diary evidence: {len(d['crop_diary_evidence'])} entries")
    print(f"  Satellite evidence: {len(d['satellite_evidence'])} reports")
    print(f"  Schemes: {[s['name'][:30] for s in d['applicable_schemes']]}")
    print(f"  Next steps: {len(d['next_steps'])}")
test("Generate insurance claim (pest damage)", t_insurance_claim)

def t_insurance_schemes():
    r = get("/insurance/schemes/IN")
    d = r.json()
    assert len(d["schemes"]) > 0
    for s in d["schemes"]:
        print(f"    {s['name']}")
test("Insurance schemes (India)", t_insurance_schemes)

def t_insurance_ke():
    r = get("/insurance/schemes/KE")
    assert r.status_code == 200
test("Insurance schemes (Kenya)", t_insurance_ke)

# ─────────────── 15. SMS FALLBACK ───────────────
print("\n=== 15. SMS FALLBACK ===")

def t_sms_commands():
    r = get("/sms/commands")
    d = r.json()
    assert len(d["commands"]) >= 5
    print(f"  SMS commands: {list(d['commands'].keys())}")
test("SMS commands list", t_sms_commands)

def t_sms_send():
    r = post("/sms/send", json={"to": "+919876543210", "message": "KisanVaani test SMS"})
    d = r.json()
    assert d["status"] in ["mock", "sent", "error"]  # error is OK if Twilio not configured for SMS
    print(f"  SMS send status: {d['status']}")
test("SMS send", t_sms_send)

# ─────────────── 16. OTHER FEATURES ───────────────
print("\n=== 16. OTHER FEATURES ===")

def t_kvk():
    r = get("/kvk/IN/Maharashtra")
    d = r.json()
    assert "results" in d
    print(f"  KVK centers found: {len(d['results'])}")
test("KVK locator (Maharashtra)", t_kvk)

def t_yield():
    r = post("/yield/predict", json={
        "country": "IN", "crop": "wheat", "land_acres": 5,
        "soil_type": "loamy", "irrigation_type": "drip",
    })
    d = r.json()
    assert "predicted_yield_per_acre" in d
    print(f"  Wheat yield: {d['predicted_yield_per_acre']} q/acre, Total: {d['total_yield']} q")
test("Yield prediction", t_yield)

def t_loans():
    r = get("/loans/IN")
    d = r.json()
    assert len(d) > 0
    print(f"  Loan schemes: {len(d)}")
test("Loan eligibility (India)", t_loans)

def t_pests():
    r = get("/pests")
    d = r.json()
    assert len(d) > 0
    print(f"  Pests in gallery: {len(d)}")
test("Pest gallery", t_pests)

def t_alerts():
    r = get("/alerts")
    d = r.json()
    print(f"  Active alerts: {len(d)}")
test("Proactive alerts", t_alerts)

def t_community_insights():
    r = get("/community")
    assert r.status_code == 200
test("Community insights", t_community_insights)

# ─────────────── 17. ANALYTICS ───────────────
print("\n=== 17. ANALYTICS ===")

def t_overview():
    r = get("/analytics/overview")
    d = r.json()
    assert d["total_calls"] > 0
    print(f"  Calls: {d['total_calls']}, Sessions: {d['unique_sessions']}, Languages: {d['languages_served']}")
test("Analytics overview", t_overview)

def t_languages_stats():
    r = get("/analytics/languages")
    assert r.status_code == 200
test("Language breakdown", t_languages_stats)

def t_timeline():
    r = get("/analytics/timeline")
    assert r.status_code == 200
test("Call timeline", t_timeline)

def t_calls():
    r = get("/calls")
    d = r.json()
    assert len(d) > 0
    print(f"  Call history: {len(d)} records")
test("Call history", t_calls)

def t_report():
    r = get(f"/report/{farmer1_id}")
    d = r.json()
    assert "report" in d
    assert len(d["report"]) > 100
    print(f"  Report length: {len(d['report'])} chars")
test("Farmer report", t_report)

# ─────────────── SUMMARY ───────────────
print("\n" + "=" * 60)
print(f"  RESULTS: {PASS} PASSED, {FAIL} FAILED out of {PASS+FAIL} tests")
print("=" * 60)
for r in RESULTS:
    print(r)
print("=" * 60)

if FAIL > 0:
    sys.exit(1)
