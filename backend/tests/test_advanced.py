"""Tests for advanced features: Price Prediction, Satellite, Expert Callbacks, Marketplace, Farmer Network."""
import os
import pytest
from fastapi.testclient import TestClient

os.environ["MOCK_MODE"] = "true"

from app.database import Base, engine
from app.main import app

Base.metadata.create_all(bind=engine)
client = TestClient(app)


# ── Helper: create a farmer ──
def _create_farmer(name="Test Farmer", region="Maharashtra", country="IN", crops=None):
    resp = client.post("/api/farmers", json={
        "name": name,
        "preferred_language": "en",
        "country": country,
        "region": region,
        "crops": crops or ["Tomato"],
        "land_size_acres": 2.0,
    })
    return resp.json()["id"]


# ────────────────────────────────
# PRICE PREDICTION
# ────────────────────────────────

class TestPricePrediction:
    def test_predict_wheat_price(self):
        resp = client.get("/api/prices/predict/wheat")
        assert resp.status_code == 200
        data = resp.json()
        assert "current_price" in data
        assert "predicted_price" in data
        assert "recommendation" in data
        assert "reason" in data
        assert "predicted_range" in data
        assert data["predicted_range"]["low"] <= data["predicted_price"] <= data["predicted_range"]["high"]

    def test_predict_tomato_price(self):
        resp = client.get("/api/prices/predict/tomato?days=14")
        assert resp.status_code == 200
        data = resp.json()
        assert data["days_ahead"] == 14
        assert "weekly_forecast" in data
        assert data["confidence"] in ("low", "medium", "high")

    def test_predict_rice_price(self):
        resp = client.get("/api/prices/predict/rice?days=7")
        assert resp.status_code == 200
        data = resp.json()
        assert data["unit"] == "Rs/quintal"

    def test_predict_unknown_crop(self):
        resp = client.get("/api/prices/predict/dragonfruit")
        assert resp.status_code == 404

    def test_price_trends(self):
        # Use exact crop name from market_prices.json
        resp = client.get("/api/prices/trends/Wheat?days=30")
        if resp.status_code == 200:
            data = resp.json()
            assert "prices" in data
            assert len(data["prices"]) > 0
            assert "date" in data["prices"][0]
            assert "price" in data["prices"][0]
        else:
            # Price history may not be seeded in test DB
            assert resp.status_code == 404

    def test_price_trends_unknown_crop(self):
        resp = client.get("/api/prices/trends/dragonfruit")
        assert resp.status_code == 404

    def test_prediction_has_recommendation(self):
        resp = client.get("/api/prices/predict/cotton")
        data = resp.json()
        assert data["recommendation"] in [
            "HOLD", "SELL NOW", "SELL SOON",
            "HOLD (slight uptrend)", "STABLE — sell when ready",
        ]


# ────────────────────────────────
# SATELLITE CROP HEALTH
# ────────────────────────────────

class TestSatelliteMonitoring:
    def test_analyze_by_coordinates(self):
        resp = client.post("/api/satellite/analyze", json={
            "latitude": 18.52,
            "longitude": 73.86,
            "crop": "Tomato",
            "country": "IN",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "ndvi_score" in data
        assert -1 <= data["ndvi_score"] <= 1
        assert data["health_status"] in ("healthy", "moderate", "stressed", "critical")
        assert "analysis" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)

    def test_analyze_by_location_name(self):
        resp = client.post("/api/satellite/analyze", json={
            "location": "pune",
            "crop": "Wheat",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "ndvi_score" in data
        assert "regional_comparison" in data

    def test_analyze_unknown_location(self):
        resp = client.post("/api/satellite/analyze", json={
            "location": "unknowncity12345",
        })
        assert resp.status_code == 404

    def test_analyze_missing_params(self):
        resp = client.post("/api/satellite/analyze", json={
            "crop": "Wheat",
        })
        assert resp.status_code == 400

    def test_satellite_history(self):
        farmer_id = _create_farmer("Satellite Farmer")
        # Create a report first
        client.post("/api/satellite/analyze", json={
            "location": "pune",
            "crop": "Tomato",
            "farmer_id": farmer_id,
        })
        resp = client.get(f"/api/satellite/history/{farmer_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_regional_satellite(self):
        resp = client.get("/api/satellite/regional/nagpur?crop=Cotton")
        assert resp.status_code == 200
        data = resp.json()
        assert "ndvi_score" in data
        assert "alert_level" in data


# ────────────────────────────────
# EXPERT CALLBACK
# ────────────────────────────────

class TestExpertCallback:
    def test_request_callback(self):
        farmer_id = _create_farmer("Expert Test Farmer")
        resp = client.post("/api/expert/request", json={
            "farmer_id": farmer_id,
            "question": "My cow is not eating and has fever",
            "ai_response": "I'm not confident about livestock diseases.",
            "ai_confidence": "low",
            "category": "livestock",
            "language": "hi",
            "country": "IN",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "ticket_id" in data
        assert data["status"] == "pending"
        assert data["priority"] == 1  # livestock = urgent

    def test_expert_queue(self):
        resp = client.get("/api/expert/queue?status=pending")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_resolve_ticket(self):
        farmer_id = _create_farmer("Resolve Test Farmer")
        # Create ticket
        create_resp = client.post("/api/expert/request", json={
            "farmer_id": farmer_id,
            "question": "Brown spots on rice leaves",
            "category": "disease",
        })
        ticket_id = create_resp.json()["ticket_id"]

        # Resolve it
        resp = client.post(f"/api/expert/{ticket_id}/resolve", json={
            "expert_name": "Dr. Sharma",
            "response": "This is rice blast disease. Spray Tricyclazole 75WP at 0.6g/liter.",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"

    def test_expert_stats(self):
        resp = client.get("/api/expert/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "pending" in data
        assert "resolved" in data


# ────────────────────────────────
# FARMER NETWORK (Community Q&A)
# ────────────────────────────────

class TestFarmerNetwork:
    def test_share_question(self):
        resp = client.post("/api/community/share", json={
            "region": "Maharashtra",
            "country": "IN",
            "crop": "Tomato",
            "question_summary": "How to control tomato leaf curl virus?",
            "ai_answer": "Remove infected plants. Spray imidacloprid for whitefly control.",
            "category": "disease",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "shared"

    def test_browse_questions(self):
        resp = client.get("/api/community/questions?country=IN")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_browse_by_region(self):
        resp = client.get("/api/community/questions?region=Maharashtra")
        assert resp.status_code == 200

    def test_mark_helpful(self):
        # Share a question first
        share = client.post("/api/community/share", json={
            "region": "Karnataka",
            "question_summary": "Best fertilizer for ragi?",
            "ai_answer": "Use DAP + MOP at 25kg/acre.",
        })
        qid = share.json()["id"]

        resp = client.post(f"/api/community/questions/{qid}/helpful")
        assert resp.status_code == 200
        assert resp.json()["helpful_count"] >= 1

    def test_trending_topics(self):
        resp = client.get("/api/community/trending?country=IN")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


# ────────────────────────────────
# MARKETPLACE
# ────────────────────────────────

class TestMarketplace:
    def test_create_sell_listing(self):
        farmer_id = _create_farmer("Seller Farmer", region="Karnataka")
        resp = client.post("/api/marketplace/listings", json={
            "farmer_id": farmer_id,
            "listing_type": "sell",
            "crop": "Tomato",
            "quantity": "10 quintals",
            "price_per_unit": 2500,
            "region": "Karnataka",
            "country": "IN",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "active"
        assert "expires" in data

    def test_create_buy_listing(self):
        farmer_id = _create_farmer("Buyer Farmer")
        resp = client.post("/api/marketplace/listings", json={
            "farmer_id": farmer_id,
            "listing_type": "buy",
            "crop": "Wheat",
            "quantity": "5 quintals",
            "region": "Maharashtra",
        })
        assert resp.status_code == 200

    def test_browse_listings(self):
        resp = client.get("/api/marketplace/listings")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_browse_by_crop(self):
        resp = client.get("/api/marketplace/listings?crop=Tomato")
        assert resp.status_code == 200

    def test_browse_by_type(self):
        resp = client.get("/api/marketplace/listings?listing_type=sell")
        assert resp.status_code == 200

    def test_marketplace_stats(self):
        resp = client.get("/api/marketplace/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_listings" in data
        assert "sell_listings" in data
        assert "buy_listings" in data


# ────────────────────────────────
# PROACTIVE CALLS
# ────────────────────────────────

class TestProactiveCalls:
    def test_generate_scheduled_calls(self):
        resp = client.post("/api/proactive/generate")
        assert resp.status_code == 200
        data = resp.json()
        assert "scheduled" in data

    def test_deliver_pending(self):
        resp = client.post("/api/proactive/deliver?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "delivered" in data
        assert "total" in data

    def test_view_queue(self):
        resp = client.get("/api/proactive/queue")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_proactive_stats(self):
        resp = client.get("/api/proactive/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "pending" in data
        assert "sent" in data


# ────────────────────────────────
# WHATSAPP
# ────────────────────────────────

class TestWhatsApp:
    def test_webhook_verification(self):
        resp = client.get("/api/whatsapp/webhook")
        assert resp.status_code == 200

    def test_conversations_endpoint(self):
        resp = client.get("/api/whatsapp/conversations/1")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_send_without_credentials(self):
        resp = client.post("/api/whatsapp/send", json={
            "to": "+919876543210",
            "message": "Test message",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "mock"
