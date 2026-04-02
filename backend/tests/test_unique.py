"""Tests for unique features: Soil Test OCR, Insurance Claims, SMS Fallback."""
import os
os.environ["MOCK_MODE"] = "true"

from fastapi.testclient import TestClient
from app.database import Base, engine
from app.main import app

Base.metadata.create_all(bind=engine)
client = TestClient(app)


def _create_farmer(name="Unique Test Farmer"):
    resp = client.post("/api/farmers", json={
        "name": name, "preferred_language": "hi", "country": "IN",
        "region": "Maharashtra", "crops": ["Tomato"], "land_size_acres": 3.0,
    })
    return resp.json()["id"]


# ── SOIL TEST OCR ──

class TestSoilOCR:
    def test_soil_interpret_values(self):
        resp = client.post("/api/soil/interpret", json={
            "ph": 6.5, "nitrogen": 120, "phosphorus": 10, "potassium": 250,
            "organic_carbon": 0.4, "crop": "Tomato",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "health" in data
        assert "issues" in data
        assert "recommendations" in data
        assert isinstance(data["issues"], list)

    def test_soil_low_ph(self):
        resp = client.post("/api/soil/interpret", json={"ph": 4.5})
        data = resp.json()
        assert data["health"] == "poor"
        assert any("acidic" in i.lower() for i in data["issues"])

    def test_soil_high_ph(self):
        resp = client.post("/api/soil/interpret", json={"ph": 9.0})
        data = resp.json()
        assert data["health"] == "poor"
        assert any("alkaline" in i.lower() for i in data["issues"])

    def test_soil_ideal(self):
        resp = client.post("/api/soil/interpret", json={
            "ph": 6.8, "nitrogen": 350, "phosphorus": 40, "potassium": 250,
            "organic_carbon": 1.0,
        })
        data = resp.json()
        assert data["health"] == "good"

    def test_soil_low_nutrients(self):
        resp = client.post("/api/soil/interpret", json={
            "nitrogen": 100, "phosphorus": 8, "potassium": 80,
        })
        data = resp.json()
        assert len(data["issues"]) >= 2  # Multiple deficiencies

    def test_soil_crop_suitability(self):
        resp = client.post("/api/soil/interpret", json={"ph": 6.5})
        data = resp.json()
        assert len(data["crop_suitability"]) > 0


# ── INSURANCE AUTO-CLAIMS ──

class TestInsuranceClaims:
    def test_generate_claim(self):
        fid = _create_farmer("Insurance Farmer")
        # Add diary entry
        client.post("/api/diary", json={
            "farmer_id": fid, "crop": "Tomato", "activity": "planted",
            "details": "500 seedlings", "date": "2026-03-01",
        })
        # Add expense
        client.post("/api/expenses", json={
            "farmer_id": fid, "category": "seeds", "amount": 3000,
            "description": "Tomato seedlings", "crop": "Tomato",
        })

        resp = client.post("/api/insurance/claim", json={
            "farmer_id": fid, "crop": "Tomato", "damage_type": "pest",
            "damage_description": "Fall armyworm destroyed 60% of crop",
            "country": "IN",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "claim_id" in data
        assert "farmer_details" in data
        assert "crop_details" in data
        assert "damage_details" in data
        assert "financial_evidence" in data
        assert "crop_diary_evidence" in data
        assert "applicable_schemes" in data
        assert "next_steps" in data
        assert len(data["next_steps"]) > 0

    def test_claim_has_schemes(self):
        fid = _create_farmer("Scheme Farmer")
        resp = client.post("/api/insurance/claim", json={
            "farmer_id": fid, "crop": "Wheat", "damage_type": "drought",
            "damage_description": "No rain for 3 weeks", "country": "IN",
        })
        data = resp.json()
        assert len(data["applicable_schemes"]) > 0
        scheme = data["applicable_schemes"][0]
        assert "name" in scheme
        assert "required_documents" in scheme
        assert "contact" in scheme

    def test_claim_invalid_farmer(self):
        resp = client.post("/api/insurance/claim", json={
            "farmer_id": 99999, "crop": "Wheat", "damage_type": "flood",
            "damage_description": "Flooded", "country": "IN",
        })
        assert resp.status_code == 404

    def test_insurance_schemes_india(self):
        resp = client.get("/api/insurance/schemes/IN")
        assert resp.status_code == 200
        data = resp.json()
        assert "schemes" in data
        assert len(data["schemes"]) > 0

    def test_insurance_schemes_kenya(self):
        resp = client.get("/api/insurance/schemes/KE")
        assert resp.status_code == 200

    def test_insurance_schemes_unknown(self):
        resp = client.get("/api/insurance/schemes/XX")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data.get("schemes", [])) == 0


# ── SMS FALLBACK ──

class TestSMSFallback:
    def test_sms_commands_list(self):
        resp = client.get("/api/sms/commands")
        assert resp.status_code == 200
        data = resp.json()
        assert "commands" in data
        assert "HELP" in data["commands"]
        assert "REGISTER" in data["commands"]
        assert "PRICE" in data["commands"]

    def test_sms_send_mock(self):
        resp = client.post("/api/sms/send", json={
            "to": "+919876543210", "message": "Test SMS from KisanVaani",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "mock"
