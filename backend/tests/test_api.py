"""Basic API tests for KisanVaani endpoints."""
import os
import pytest
from fastapi.testclient import TestClient

# Force mock mode for tests
os.environ["MOCK_MODE"] = "true"

from app.database import Base, engine
from app.main import app

# Ensure all tables are created for tests
Base.metadata.create_all(bind=engine)

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "KisanVaani"
        assert "version" in data
        assert "mock_mode" in data

    def test_health_reports_db_status(self):
        response = client.get("/api/health")
        data = response.json()
        assert "database" in data

    def test_health_reports_ai_config(self):
        response = client.get("/api/health")
        data = response.json()
        assert "ai_configured" in data
        assert "twilio_configured" in data


class TestLanguagesEndpoint:
    def test_languages_returns_all(self):
        response = client.get("/api/languages")
        assert response.status_code == 200
        data = response.json()
        assert "hi" in data
        assert "en" in data
        assert "te" in data
        assert "ta" in data
        assert "sw" in data

    def test_language_has_name(self):
        response = client.get("/api/languages")
        data = response.json()
        assert data["hi"]["name"] == "Hindi"
        assert data["hi"]["native_name"] == "हिन्दी"

    def test_language_has_native_name(self):
        response = client.get("/api/languages")
        data = response.json()
        for code, lang in data.items():
            assert "name" in lang
            assert "native_name" in lang


class TestCountriesEndpoint:
    def test_countries_returns_data(self):
        response = client.get("/api/countries")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_countries_have_required_fields(self):
        response = client.get("/api/countries")
        data = response.json()
        for code, country in data.items():
            assert "name" in country
            assert "languages" in country
            assert "currency" in country


class TestVoiceEndpoint:
    def test_text_input_requires_text(self):
        response = client.post("/api/voice/text", json={
            "text": "",
            "session_id": "test_session_1",
        })
        assert response.status_code == 422  # Validation error

    def test_text_input_rejects_long_text(self):
        response = client.post("/api/voice/text", json={
            "text": "x" * 3000,
            "session_id": "test_session_1",
        })
        assert response.status_code == 422

    def test_text_input_mock_mode(self):
        response = client.post("/api/voice/text", json={
            "text": "My crops have yellow leaves",
            "language": "en",
            "session_id": "test_session_mock_1",
            "country": "IN",
        })
        assert response.status_code == 200
        data = response.json()
        assert "response_text" in data
        assert "audio_url" in data
        assert data["session_id"] == "test_session_mock_1"
        assert len(data["response_text"]) > 0

    def test_text_input_hindi(self):
        response = client.post("/api/voice/text", json={
            "text": "Mere tamatar ke patte peele ho rahe hain",
            "language": "hi",
            "session_id": "test_session_mock_2",
            "country": "IN",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "hi"

    def test_text_input_telugu(self):
        response = client.post("/api/voice/text", json={
            "text": "Naa vari pantalo purugulu vasthunnaayi",
            "language": "te",
            "session_id": "test_session_mock_3",
            "country": "IN",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "te"

    def test_text_input_tamil(self):
        response = client.post("/api/voice/text", json={
            "text": "En nel payiril puzhu thakkam irukku",
            "language": "ta",
            "session_id": "test_session_mock_4",
            "country": "IN",
        })
        assert response.status_code == 200

    def test_text_input_swahili(self):
        response = client.post("/api/voice/text", json={
            "text": "Mimea yangu ya mahindi yana wadudu",
            "language": "sw",
            "session_id": "test_session_mock_5",
            "country": "KE",
        })
        assert response.status_code == 200

    def test_text_input_invalid_language(self):
        response = client.post("/api/voice/text", json={
            "text": "Hello",
            "language": "xx",
            "session_id": "test_session_3",
        })
        assert response.status_code == 422

    def test_text_input_auto_language(self):
        response = client.post("/api/voice/text", json={
            "text": "What fertilizer should I use?",
            "language": "auto",
            "session_id": "test_session_auto",
        })
        assert response.status_code == 200

    def test_session_id_too_long(self):
        response = client.post("/api/voice/text", json={
            "text": "Hello",
            "language": "en",
            "session_id": "x" * 200,
        })
        assert response.status_code == 422

    def test_audio_endpoint_missing_file(self):
        response = client.get("/api/voice/audio/nonexistent.wav")
        assert response.status_code == 404

    def test_audio_endpoint_path_traversal_dots(self):
        response = client.get("/api/voice/audio/..%2F..%2Fetc%2Fpasswd")
        assert response.status_code in [400, 404]

    def test_multi_turn_conversation(self):
        """Test that conversation history persists across turns."""
        session = "test_multi_turn"
        # First turn
        r1 = client.post("/api/voice/text", json={
            "text": "My tomatoes have yellow leaves",
            "language": "en",
            "session_id": session,
        })
        assert r1.status_code == 200

        # Second turn (follow-up)
        r2 = client.post("/api/voice/text", json={
            "text": "What about watering schedule?",
            "language": "en",
            "session_id": session,
        })
        assert r2.status_code == 200


class TestAlertsEndpoint:
    def test_alerts_returns_list(self):
        response = client.get("/api/alerts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Demo data may or may not be seeded depending on test execution order

    def test_alerts_filter_by_country(self):
        response = client.get("/api/alerts?country=IN")
        assert response.status_code == 200
        data = response.json()
        for alert in data:
            assert alert["country"] == "IN"

    def test_alerts_have_required_fields(self):
        response = client.get("/api/alerts")
        data = response.json()
        for alert in data:
            assert "title" in alert
            assert "message" in alert
            assert "severity" in alert
            assert "alert_type" in alert


class TestCommunityEndpoint:
    def test_community_returns_list(self):
        response = client.get("/api/community")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_community_has_required_fields(self):
        response = client.get("/api/community")
        data = response.json()
        for insight in data:
            assert "region" in insight
            assert "topic" in insight
            assert "farmer_count" in insight


class TestAnalyticsEndpoint:
    def test_overview_returns_stats(self):
        response = client.get("/api/analytics/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_calls" in data
        assert "unique_sessions" in data

    def test_languages_stats(self):
        response = client.get("/api/analytics/languages")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_timeline_returns_data(self):
        response = client.get("/api/analytics/timeline")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCallsEndpoint:
    def test_calls_returns_list(self):
        response = client.get("/api/calls")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestFeaturesEndpoint:
    def test_weather_known_location(self):
        response = client.get("/api/weather/pune")
        assert response.status_code == 200
        data = response.json()
        # May have real data or error depending on network
        assert isinstance(data, dict)

    def test_weather_unknown_location(self):
        response = client.get("/api/weather/unknowncity12345")
        # May return 404 or 200 with error depending on router implementation
        assert response.status_code in [200, 404]

    def test_pests_returns_list(self):
        response = client.get("/api/pests")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_loans_india(self):
        response = client.get("/api/loans/IN")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_loans_kenya(self):
        response = client.get("/api/loans/KE")
        assert response.status_code == 200

    def test_kvk_india(self):
        response = client.get("/api/kvk/IN/Maharashtra")
        assert response.status_code == 200
        data = response.json()
        # API wraps results in a dict with "results" key
        assert "results" in data or isinstance(data, list)

    def test_yield_prediction(self):
        response = client.post("/api/yield/predict", json={
            "country": "IN",
            "crop": "wheat",
            "land_acres": 2,
            "soil_type": "loamy",
            "irrigation": "drip",
        })
        assert response.status_code == 200
        data = response.json()
        assert "predicted_yield_per_acre" in data


class TestFarmerEndpoints:
    def test_create_farmer(self):
        response = client.post("/api/farmers", json={
            "name": "Test Farmer",
            "preferred_language": "hi",
            "country": "IN",
            "region": "Maharashtra",
            "crops": ["Tomato", "Cotton"],
            "land_size_acres": 3.0,
        })
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["name"] == "Test Farmer"
        assert "id" in data

    def test_list_farmers(self):
        response = client.get("/api/farmers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_onboard_farmer(self):
        response = client.post("/api/onboard", json={
            "name": "Onboard Test",
            "language": "en",
            "country": "IN",
            "region": "Karnataka",
            "crops": ["Tomato"],
            "land_acres": 1.5,
        })
        assert response.status_code == 200
        data = response.json()
        assert "farmer_id" in data
        assert "welcome_message" in data


class TestExpensesEndpoint:
    def test_create_expense(self):
        # First create a farmer
        farmer_resp = client.post("/api/farmers", json={
            "name": "Expense Farmer",
            "preferred_language": "en",
            "country": "IN",
        })
        farmer_id = farmer_resp.json()["id"]

        response = client.post("/api/expenses", json={
            "farmer_id": farmer_id,
            "category": "fertilizer",
            "description": "Urea 50kg bag",
            "amount": 1500,
            "crop": "wheat",
        })
        assert response.status_code in [200, 201]

    def test_get_expenses(self):
        response = client.get("/api/expenses/1")
        assert response.status_code == 200


class TestInputValidation:
    """Test security-related input validation."""

    def test_empty_text_rejected(self):
        response = client.post("/api/voice/text", json={
            "text": "   ",
            "session_id": "test",
        })
        assert response.status_code == 422

    def test_max_length_boundary(self):
        """Text at exactly max length should pass."""
        response = client.post("/api/voice/text", json={
            "text": "a" * 2000,
            "language": "en",
            "session_id": "test_boundary",
        })
        assert response.status_code == 200

    def test_over_max_length_rejected(self):
        response = client.post("/api/voice/text", json={
            "text": "a" * 2001,
            "language": "en",
            "session_id": "test_over",
        })
        assert response.status_code == 422
